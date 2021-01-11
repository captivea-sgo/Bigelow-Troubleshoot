# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from werkzeug import urls

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    portal_payment_options = fields.Text(string='Portal Payment Options')
    stripe_payment_url = fields.Char(string='Stripe Payment Link')

    @api.multi
    def action_invoice_open(self):
        payment_acquirer = self.env['payment.acquirer']
        res = super(AccountInvoice, self).action_invoice_open()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for invoice in self:
            stripe_payment_url = urls.url_join(base_url, '/my/invoices/%s' % invoice.id)
            invoice.stripe_payment_url = stripe_payment_url
            invoice.portal_payment_options = payment_acquirer.with_context({'call_backend': True}).render_payment_block(
                invoice.number, invoice.residual, invoice.currency_id.id,
                partner_id=invoice.partner_id.id, company_id=invoice.company_id.id)
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        for invoice in self.invoice_ids:
            if invoice.type == 'out_invoice':
                invoice.portal_payment_options = self.env['payment.acquirer'].with_context({'call_backend': True}).render_payment_block(
                invoice.number, invoice.residual, invoice.currency_id.id,
                partner_id=invoice.partner_id.id, company_id=invoice.company_id.id)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
