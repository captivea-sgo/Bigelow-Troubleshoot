# Copyright 2019 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models 


class Company(models.Model):
    _inherit = "res.company"

    printnode_enabled = fields.Boolean(
        string='Print via PrintNode',
        default=False
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Printer'
    )

    printnode_recheck = fields.Boolean(
        string='Mandatory check Printing Status',
        default=False
    )


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    printnode_enabled = fields.Boolean(
        string='Print via PrintNode',
        readonly=False,
        related='company_id.printnode_enabled'
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Printer',
        readonly=False,
        related='company_id.printnode_printer'
    )

    printnode_recheck = fields.Boolean(
        string='Mandatory check Printing Status',
        readonly=False,
        related='company_id.printnode_recheck'
    )
