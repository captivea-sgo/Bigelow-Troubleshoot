###################################################################################
#
#    Copyright (C) 2017 MuK IT GmbH
#
#    Odoo Proprietary License v1.0
#    
#    This software and associated files (the "Software") may only be used 
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from the authors, typically via Odoo Apps,
#    or if you have received a written agreement from the authors of the
#    Software (see the COPYRIGHT file).
#    
#    You may develop Odoo modules that use the Software as a library 
#    (typically by depending on it, importing it and using its resources),
#    but without copying any source code or material from the Software.
#    You may distribute those modules under the license of your choice,
#    provided that this license is compatible with the terms of the Odoo
#    Proprietary License (For example: LGPL, MIT, or proprietary licenses
#    similar to this one).
#    
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#    
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#    
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################

import logging
import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    
    _inherit = 'res.users'

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    oauth1_sessions = fields.Integer(
        compute='_compute_oauth1_sessions',
        string="OAuth1 Sessions")
    
    oauth2_sessions = fields.Integer(
        compute='_compute_oauth2_sessions',
        string="OAuth2 Sessions")
    
    #----------------------------------------------------------
    # Framework
    #----------------------------------------------------------
    
    def __init__(self, pool, cr):
        init_result = super(ResUsers, self).__init__(pool, cr)
        oauth_fields = ['oauth1_sessions', 'oauth2_sessions']
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(oauth_fields)
        return init_result

    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------
    
    def _compute_oauth1_sessions(self):
        for record in self:
            model = self.env['muk_rest.access_token']
            domain = [('user', '=', self.env.uid)]
            record.oauth1_sessions = model.search(domain, count=True)
            
    def _compute_oauth2_sessions(self):
        for record in self:
            model = self.env['muk_rest.bearer_token']
            domain = [
                '&', ('user', '=', self.env.uid),
                '|', ('expires_in', '=', False), ('expires_in', '>', datetime.datetime.utcnow())
            ]
            record.oauth2_sessions = model.search(domain, count=True)