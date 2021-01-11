# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
import pprint
import requests

from odoo import api, fields, models, _
from odoo.tools import float_round, float_repr

_logger = logging.getLogger(__name__)

def _partner_format_address(address1=False, address2=False):
    return ' '.join((address1 or '', address2 or '')).strip()

def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]

STRIPE_HEADERS = {'Stripe-Version': '2016-03-07'}

# The following currencies are integer only, see https://stripe.com/docs/currencies#zero-decimal
INT_CURRENCIES = [
    u'BIF', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
]


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    backend_view_template_id = fields.Many2one('ir.ui.view', string='Backend Form Button Template')
    auto_payment = fields.Selection([
        ('none', 'No automatic payment'),
        ('generate_and_pay_invoice', 'Automatic pay invoice on acquirer confirmation')],
        string='Invoice Payment', default='none', required=True)

    def _wrap_payment_block(self, html_block, amount, currency_id):
        payment_header = _('Pay safely online')
        amount_str = float_repr(amount, self.env['decimal.precision'].precision_get('Account'))
        currency = self.env['res.currency'].browse(currency_id)
        currency_str = currency.symbol or currency.name
        amount = u"%s %s" % ((currency_str, amount_str) if currency.position == 'before' else (amount_str, currency_str))
        result = u"""<div class="payment_acquirers">
                 <div class="payment_header">
                     <div class="payment_amount">%s</div>
                     %s
                 </div>
                 %%s
             </div>""" % (amount, payment_header)
        return result % html_block.decode("utf-8")

    def render_payment_block(self, reference, amount, currency_id, tx_id=None, partner_id=False, partner_values=None, tx_values=None, company_id=None):
        html_forms = []
        domain = [('website_published', '=', True), ('provider', '=', 'stripe')]
        if company_id:
            domain.append(('company_id', '=', company_id))
        acquirer_ids = self.search(domain)
        for acquirer_id in acquirer_ids:
            button = acquirer_id.render(
                reference, amount, currency_id,
                partner_id, tx_values)
            html_forms.append(button)
        if not html_forms:
            return ''
        html_block = (b'\n').join(html_forms)
        return self._wrap_payment_block(html_block, amount, currency_id)

    @api.multi
    def stripe_form_generate_values(self, tx_values):
        self.ensure_one()
        if self._context.get('call_backend'):
            stripe_tx_values = dict(tx_values)
            temp_stripe_tx_values = {
                'partner_id': tx_values['partner_id'],
                'company': self.company_id.name,
                'amount': tx_values['amount'],  # Mandatory
                'currency': tx_values['currency'].name,  # Mandatory anyway
                'currency_id': tx_values['currency'].id,  # same here
                'address_line1': tx_values.get('partner_address'),  # Any info of the partner is not mandatory
                'address_city': tx_values.get('partner_city'),
                'address_country': tx_values.get('partner_country') and tx_values.get('partner_country').name or '',
                'email': tx_values.get('partner_email'),
                'address_zip': tx_values.get('partner_zip'),
                'name': tx_values.get('partner_name'),
                'phone': tx_values.get('partner_phone'),
            }

            stripe_tx_values.update(temp_stripe_tx_values)
            return stripe_tx_values
        return super(PaymentAcquirer, self).stripe_form_generate_values(tx_values=tx_values)

    @api.multi
    def render(self, reference, amount, currency_id, partner_id=False, values=None):
        """ Renders the form template of the given acquirer as a qWeb template.
        :param string reference: the transaction reference
        :param float amount: the amount the buyer has to pay
        :param currency_id: currency id
        :param dict partner_id: optional partner_id to fill values
        :param dict values: a dictionary of values for the transction that is
        given to the acquirer-specific method generating the form values

        All templates will receive:

         - acquirer: the payment.acquirer browse record
         - user: the current user browse record
         - currency_id: id of the transaction currency
         - amount: amount of the transaction
         - reference: reference of the transaction
         - partner_*: partner-related values
         - partner: optional partner browse record
         - 'feedback_url': feedback URL, controler that manage answer of the acquirer (without base url) -> FIXME
         - 'return_url': URL for coming back after payment validation (wihout base url) -> FIXME
         - 'cancel_url': URL if the client cancels the payment -> FIXME
         - 'error_url': URL if there is an issue with the payment -> FIXME
         - context: Odoo context

        """
        if values is None:
            values = {}

        values.setdefault('return_url', '/payment/process')
        # reference and amount
        values.setdefault('reference', reference)
        amount = float_round(amount, 2)
        values.setdefault('amount', amount)

        # currency id
        currency_id = values.setdefault('currency_id', currency_id)
        if currency_id:
            currency = self.env['res.currency'].browse(currency_id)
        else:
            currency = self.env.user.company_id.currency_id
        values['currency'] = currency

        # Fill partner_* using values['partner_id'] or partner_id argument
        partner_id = values.get('partner_id', partner_id)
        billing_partner_id = values.get('billing_partner_id', partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner_id != billing_partner_id:
                billing_partner = self.env['res.partner'].browse(billing_partner_id)
            else:
                billing_partner = partner
            values.update({
                'partner': partner,
                'partner_id': partner_id,
                'partner_name': partner.name,
                'partner_lang': partner.lang,
                'partner_email': partner.email,
                'partner_zip': partner.zip,
                'partner_city': partner.city,
                'partner_address': _partner_format_address(partner.street, partner.street2),
                'partner_country_id': partner.country_id.id,
                'partner_country': partner.country_id,
                'partner_phone': partner.phone,
                'partner_state': partner.state_id,
                'billing_partner': billing_partner,
                'billing_partner_id': billing_partner_id,
                'billing_partner_name': billing_partner.name,
                'billing_partner_commercial_company_name': billing_partner.commercial_company_name,
                'billing_partner_lang': billing_partner.lang,
                'billing_partner_email': billing_partner.email,
                'billing_partner_zip': billing_partner.zip,
                'billing_partner_city': billing_partner.city,
                'billing_partner_address': _partner_format_address(billing_partner.street, billing_partner.street2),
                'billing_partner_country_id': billing_partner.country_id.id,
                'billing_partner_country': billing_partner.country_id,
                'billing_partner_phone': billing_partner.phone,
                'billing_partner_state': billing_partner.state_id,
            })
        if values.get('partner_name'):
            values.update({
                'partner_first_name': _partner_split_name(values.get('partner_name'))[0],
                'partner_last_name': _partner_split_name(values.get('partner_name'))[1],
            })
        if values.get('billing_partner_name'):
            values.update({
                'billing_partner_first_name': _partner_split_name(values.get('billing_partner_name'))[0],
                'billing_partner_last_name': _partner_split_name(values.get('billing_partner_name'))[1],
            })

        # Fix address, country fields
        if not values.get('partner_address'):
            values['address'] = _partner_format_address(values.get('partner_street', ''), values.get('partner_street2', ''))
        if not values.get('partner_country') and values.get('partner_country_id'):
            values['country'] = self.env['res.country'].browse(values.get('partner_country_id'))
        if not values.get('billing_partner_address'):
            values['billing_address'] = _partner_format_address(values.get('billing_partner_street', ''), values.get('billing_partner_street2', ''))
        if not values.get('billing_partner_country') and values.get('billing_partner_country_id'):
            values['billing_country'] = self.env['res.country'].browse(values.get('billing_partner_country_id'))

        # compute fees
        fees_method_name = '%s_compute_fees' % self.provider
        if hasattr(self, fees_method_name):
            fees = getattr(self, fees_method_name)(values['amount'], values['currency_id'], values.get('partner_country_id'))
            values['fees'] = float_round(fees, 2)

        # call <name>_form_generate_values to update the tx dict with acqurier specific values
        cust_method_name = '%s_form_generate_values' % (self.provider)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)

        values.update({
            'tx_url': self._context.get('tx_url', self.get_form_action_url()),
            'submit_class': self._context.get('submit_class', 'btn btn-link'),
            'submit_txt': self._context.get('submit_txt'),
            'acquirer': self,
            'user': self.env.user,
            'context': self._context,
            'type': values.get('type') or 'form',
        })

        _logger.info('payment.acquirer.render: <%s> values rendered for form payment:\n%s', self.provider, pprint.pformat(values))
        # Change(s) add to the replaced method.
        if self.backend_view_template_id and self._context.get('call_backend'):
            return self.backend_view_template_id.render(values, engine='ir.qweb')
        return self.view_template_id.render(values, engine='ir.qweb')


class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'

    def _create_stripe_charge(self, acquirer_ref=None, tokenid=None, email=None):
        if self._context.get('is_backend_pay'):
            api_url_charge = 'https://%s/charges' % (self.acquirer_id._get_stripe_api_url())
            charge_params = {
                'amount': int(self.amount if self.currency_id.name in INT_CURRENCIES else float_round(self.amount * 100, 2)),
                'currency': self.currency_id.name,
                'metadata[reference]': self.reference,
                'description': self.reference,
            }
            if acquirer_ref:
                charge_params['customer'] = acquirer_ref
            if tokenid:
                charge_params['card'] = str(tokenid)
            if email:
                charge_params['receipt_email'] = email.strip()

            _logger.info('_create_stripe_charge: Sending values to URL %s, values:\n%s', api_url_charge, pprint.pformat(charge_params))
            r = requests.post(api_url_charge,
                              auth=(self.acquirer_id.stripe_secret_key, ''),
                              params=charge_params,
                              headers=STRIPE_HEADERS)
            res = r.json()
            _logger.info('_create_stripe_charge: Values received:\n%s', pprint.pformat(res))
            return res
        return super(PaymentTransactionStripe, self)._create_stripe_charge(acquirer_ref=acquirer_ref, tokenid=tokenid, email=email)

    @api.model
    def _stripe_form_get_tx_from_data(self, data):
        """ Given a data dict coming from stripe, verify it and find the related
        transaction record. """
        if self._context.get('is_backend_pay'):
            reference = data.get('metadata', {}).get('reference')
            if not reference:
                stripe_error = data.get('error', {}).get('message', '')
                _logger.error('Stripe: invalid reply received from stripe API, looks like '
                              'the transaction failed. (error: %s)', stripe_error  or 'n/a')
                error_msg = _("We're sorry to report that the transaction has failed.")
                if stripe_error:
                    error_msg += " " + (_("Stripe gave us the following info about the problem: '%s'") %
                                        stripe_error)
                error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
                                     "credit card details, or contacting your bank?")
                raise ValidationError(error_msg)

            tx = self.search([('reference', '=', reference)])
            if not tx:
                error_msg = (_('Stripe: no order found for reference %s') % reference)
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            elif len(tx) > 1:
                error_msg = (_('Stripe: %s orders found for reference %s') % (len(tx), reference))
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            return tx[0]
        return super(PaymentTransactionStripe, self)._stripe_form_get_tx_from_data(data=data)

    @api.multi
    def _stripe_form_get_invalid_parameters(self, data):
        if self._context.get('is_backend_pay'):
            invalid_parameters = []
            reference = data['metadata']['reference']
            if reference != self.reference:
                invalid_parameters.append(('Reference', reference, self.reference))
            return invalid_parameters
        return super(PaymentTransactionStripe, self)._stripe_form_get_invalid_parameters(data=data)

    @api.multi
    def _stripe_s2s_validate_tree(self, tree):
        self.ensure_one()
        if self._context.get('is_backend_pay'):
            if self.state != 'draft':
                _logger.info('Stripe: trying to validate an already validated tx (ref %s)', self.reference)
                return True

            status = tree.get('status')
            if status == 'succeeded':
                self.write({
                    'date': fields.datetime.now(),
                    'acquirer_reference': tree.get('id'),
                })
                self._set_transaction_done()
                self.execute_callback()
                if self.payment_token_id:
                    self.payment_token_id.verified = True
                return True
            else:
                error = tree['error']['message']
                _logger.warn(error)
                self.sudo().write({
                    'state_message': error,
                    'acquirer_reference': tree.get('id'),
                    'date': fields.datetime.now(),
                })
                self._set_transaction_cancel()
                return False
        return super(PaymentTransactionStripe, self)._stripe_s2s_validate_tree(tree=tree)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
