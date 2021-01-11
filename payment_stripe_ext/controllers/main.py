# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
import pprint
import werkzeug
import json

from odoo import http, tools, _
from odoo.http import request

from odoo.addons.payment_stripe.controllers.main import StripeController
from odoo.addons.payment.controllers.portal import PaymentProcessing

_logger = logging.getLogger(__name__)

def _get_invoice_id(tx):
    invoice = False
    reference = tx.reference.split('-')
    if 'x' in tx.reference:
        reference = tx.reference.split('x')
    if reference:
        invoice = request.env['account.invoice'].sudo().search([('number', '=', reference[0])], limit=1)
    return invoice


class StripeController(StripeController):

    @http.route(['/payment/stripe/create_charge'], type='json', auth='public')
    def stripe_create_charge(self, **post):
        """ Create a payment transaction
        Expects the result from the user input from checkout.js popup"""
        if post.get('is_backend_pay'):
            TX = request.env['payment.transaction']
            tx = None
            if post.get('tx_ref'):
                tx = TX.sudo().search([('reference', '=', post['tx_ref'])])
            if not tx:
                tx_id = (post.get('tx_id') or request.session.get('sale_transaction_id') or
                         request.session.get('website_payment_tx_id'))
                tx = TX.sudo().browse(int(tx_id))
            if not tx:
                raise werkzeug.exceptions.NotFound()

            stripe_token = post['token']
            response = None
            if tx.type == 'form_save' and tx.partner_id:
                payment_token_id = request.env['payment.token'].sudo().create({
                    'acquirer_id': tx.acquirer_id.id,
                    'partner_id': tx.partner_id.id,
                    'stripe_token': stripe_token
                })
                tx.payment_token_id = payment_token_id
                response = tx.with_context(is_backend_pay=True)._create_stripe_charge(acquirer_ref=payment_token_id.acquirer_ref, email=stripe_token['email'])
            else:
                response = tx.with_context(is_backend_pay=True)._create_stripe_charge(tokenid=stripe_token['id'], email=stripe_token['email'])
            _logger.info('Stripe: entering form_feedback with post data %s', pprint.pformat(response))
            if response:
                request.env['payment.transaction'].sudo().with_context(lang=None, is_backend_pay=True).form_feedback(response, 'stripe')
            # add the payment transaction into the session to let the page /payment/process to handle it
            PaymentProcessing.add_payment_transaction(tx)
            if tx:
                invoice = _get_invoice_id(tx=tx)
                if invoice:
                    if invoice.state == 'open' and tx.acquirer_id and tx.acquirer_id.provider == 'stripe' and tx.acquirer_id.auto_payment == 'generate_and_pay_invoice' and tx.acquirer_id.journal_id:
                        tx._cron_post_process_after_done()
                    invoice_view = request.env.ref('account.invoice_tree')
                    tx.update({'is_processed': True})
                    action_id = request.env['ir.actions.act_window'].sudo().search([('view_id', '=', invoice_view.id)], limit=1)
                    invoice_url = '/web?#id=%s&action=%s&model=account.invoice&view_type=form&menu_id=%s' % (invoice[0].id, str(action_id.id), request.env.ref('account.menu_finance').id)
                    if request.session.get('from_backend'):
                        request.session.pop('from_backend', False)
                        return invoice_url
                    else:
                        return '/my/invoices/%s' % (invoice.id)
            return '/payment/process'
        return super(StripeController, self).stripe_create_charge(**post)


class PaymentStripe(http.Controller):

    @http.route(['/payment_stripe/transaction'], type='json', auth="public", website=True)
    def transaction(self, reference, amount, currency_id, acquirer_id, partner=None):
        if partner:
            partner_id = int(partner)
        elif not partner:
            partner_id = request.env.user.partner_id.id if request.env.user.partner_id != request.website.partner_id else False
        acquirer = request.env['payment.acquirer'].browse(int(acquirer_id))
        invoice = request.env['account.invoice'].search([('number','=', reference)], limit=1)
        reference_values = invoice and {'invoice_ids': [(4, invoice)]} or {}
        reference = request.env['payment.transaction']._compute_reference(values=reference_values, prefix=invoice.number)
        values = {
            'acquirer_id': int(acquirer_id),
            'reference': reference,
            'amount': float(amount),
            'currency_id': int(currency_id),
            'partner_id': partner_id,
            'type': 'form_save' if acquirer.save_token != 'none' and partner_id else 'form',
        }
        tx = request.env['payment.transaction'].sudo().create(values)
        invoice = _get_invoice_id(tx=tx)
        tx.update({'invoice_ids': [(6, 0, [invoice.id])]})
        PaymentProcessing.add_payment_transaction(tx)
        request.session['website_payment_tx_id'] = tx.id
        request.session['from_backend'] = True
        return tx.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
