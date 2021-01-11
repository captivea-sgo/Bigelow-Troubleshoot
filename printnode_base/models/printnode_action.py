# Copyright 2019 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields


class PrintNodeActionButton(models.Model):
    """ Call Button
    """
    _name = 'printnode.action.button'
    _description = 'PrintNode Action Button'

    _rec_name = 'report_id'

    active = fields.Boolean(
        'Active', default=True,
        help="""Activate or Deactivate the print action button.
                If no active then move to the status \'archive\'.
                Still can by found using filters button"""
    )

    description = fields.Char(
        string='Description',
        size=64,
        help="""Text field for notes and memo."""
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model'
    )

    model = fields.Char(
        string='Related Document Model',
        related='model_id.model',
        help="""Choose a model where the button is placed. You can find the
                model name in the URL. For example the model of this page is
                \'model=printnode.action.button\'.
                Check this in the URL after the \'model=\'."""
    )

    method = fields.Char(
        string='Method',
        size=64
    )

    method_id = fields.Many2one(
        'printnode.action.method',
        string='Method',
        help="""The technical name of the action that a button performs.
                It can be seen only in debug mode. Hover the cursor on
                the desired button using debug mode and type a method name
                in this field."""
    )

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report',
        help="""Choose a report that will be printed after you hit a button"""
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer'
    )

    preprint = fields.Boolean(
        'Print before action',
        help="""By default the report will be printed after your action.
                First you click a button, server make the action then print
                result of this. If you want to print first and only after
                that make an action assigned to the button, then activate
                this field. Valid per each action (button)."""
    )


class PrintNodeActionMethod(models.Model):
    """
    """
    _name = 'printnode.action.method'
    _description = 'PrintNode Action Method'

    name = fields.Char(
        string='Name',
        size=64
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model'
    )

    method = fields.Char(
        string='Method',
        size=64
    )
