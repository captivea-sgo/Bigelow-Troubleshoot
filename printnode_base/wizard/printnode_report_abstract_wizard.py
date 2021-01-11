# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models, _
from odoo.exceptions import UserError


class PrintnodeReportAbstractWizard(models.AbstractModel):
    _name = 'printnode.report.abstract.wizard'
    _description = 'Print Report via PrintNode'

    number_copy = fields.Integer(
        default=1,
        string='Copies',
    )

    number_copy_selectable = fields.Boolean(
        default=lambda self: self.get_number_copy_selectable(),
    )

    printer_id = fields.Many2one(
        comodel_name='printnode.printer',
        default=lambda self: self.env.user.printnode_printer.id,
    )

    status = fields.Char(
        related='printer_id.status',
    )

    def get_number_copy_selectable(self):
        # return Boolean
        return False

    def get_attachment(self):
        # return (ir.attachment, params)
        return (None, None)

    def get_report(self):
        # return ir.actions.report
        return False

    def get_docids(self):
        # return list
        return []

    def do_print(self):
        self.ensure_one()

        # first try to print specified attachment
        attachment, params = self.get_attachment()

        if isinstance(params, str):
            params = {'title': params}

        if attachment is not None:
            return self._print_attachment(attachment, params)

        # if no attachment specified than try to print report
        return self._print_report()

    def _print_attachment(self, attachment, params):
        if not attachment:
            raise UserError(_('No attachment found.'))

        if not self.printer_id:
            if self.number_copy > 1:
                raise UserError(_(
                    'Only 1 copy can be downloaded '
                    'when printer is not selected.'
                ))

            return {
                'type': 'ir.actions.act_url',
                'name': params.get('title'),
                'url': '/web/content/%s?download=true' % attachment.id,
            }

        params.update({'copies': self.number_copy})

        self.printer_id.printnode_print_pdf_b64(
            data=attachment.datas.decode('utf-8'),
            params=params
        )

        return {'type': 'ir.actions.act_window_close'}

    def _print_report(self):
        report = self.get_report()
        docids = self.get_docids()

        # add copies
        for i in range(self.number_copy - 1):
            docids += self.get_docids()

        # if no printer than download PDF
        if not self.printer_id:
            return report.report_action(
                docids=docids
            )

        # if printer than send to printnode
        self.printer_id.printnode_print(
            report,
            docids,
        )

        return {'type': 'ir.actions.act_window_close'}
