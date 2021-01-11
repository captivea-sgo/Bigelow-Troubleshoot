# Copyright 2019 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields


class User(models.Model):
    """ User entity. Add 'Default Printer' field (no restrictions).
    """
    _inherit = 'res.users'

    printnode_enabled = fields.Boolean(
    	string='Print via PrintNode',
    	default=False
    )

    printnode_printer = fields.Many2one(
    	'printnode.printer',
    	string='Default Printer'
    )

    def __init__(self, pool, cr):
        init_res = super(User, self).__init__(pool, cr)
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(['printnode_enabled', 'printnode_printer'])
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(['printnode_enabled', 'printnode_printer'])
        return init_res
