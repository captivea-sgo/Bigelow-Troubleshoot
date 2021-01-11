# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        _logger.warning("Start!!!")
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}
        _logger.warning("1")

        # Keep track of the sequences of the lines
        # To keep lines under their section
        inv_line_sequence = 0
        for order in self:
            _logger.warning("2")
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least one invoiceable line
            pending_section = None

            # Create lines in batch to avoid performance problems
            line_vals_list = []
            _logger.warning("3")
            # sequence is the natural order of order_lines
            for line in order.order_line:
                _logger.warning("4")
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                _logger.warning("5")
                if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                _logger.warning("6")
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                _logger.warning("7")
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)
                _logger.warning("8")
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                    _logger.warning("9")
                    if pending_section:
                        _logger.warning("10")
                        section_invoice = pending_section.invoice_line_create_vals(
                            invoices[group_key].id,
                            pending_section.qty_to_invoice
                        )
                        inv_line_sequence += 1
                        section_invoice[0]['sequence'] = inv_line_sequence
                        line_vals_list.extend(section_invoice)
                        pending_section = None
                    _logger.warning("11")
                    inv_line_sequence += 1
                    inv_line = line.invoice_line_create_vals(
                        invoices[group_key].id, line.qty_to_invoice
                    )
                    _logger.warning("11.5")
                    inv_line[0]['sequence'] = inv_line_sequence
                    line_vals_list.extend(inv_line)
            _logger.warning("12")
            if references.get(invoices.get(group_key)):
                _logger.warning("13")
                if order not in references[invoices[group_key]]:
                    _logger.warning("14")
                    references[invoices[group_key]] |= order
            _logger.warning("15")
            self.env['account.invoice.line'].create(line_vals_list)
            _logger.warning("16")

        for group_key in invoices:
            _logger.warning("17")
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key])[:2000],
                                       'origin': ', '.join(invoices_origin[group_key])})
            _logger.warning("18")
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                _logger.warning("19")
                invoices[group_key].reference = sale_orders.reference
        _logger.warning("20")
        if not invoices:
            _logger.warning("21")
            raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        _logger.warning("22")
        self._finalize_invoices(invoices, references)
        _logger.warning("END!!!!")
        return [inv.id for inv in invoices.values()]