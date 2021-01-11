##################################################################################
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

import os
import json
import urllib
import logging
import requests
import unittest

import requests

from odoo import _, SUPERUSER_ID
from odoo.tests import common

from odoo.addons.muk_rest import validators, tools
from odoo.addons.muk_rest.tests.common import active_authentication, RestfulCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

class WriteTestCase(RestfulCase):
    
    @unittest.skipIf(not active_authentication, "Skipped because no authentication is available!")
    def test_write(self):
        client = self.authenticate()
        ids = json.dumps([2])
        values = json.dumps({'name': 'Restful Partner'})
        response = client.put(self.write_url, data={'model': 'res.partner', 'ids': ids, 'values': values})
        tester = self.env['res.partner'].browse([2]).name
        self.assertTrue(response)
        self.assertEquals('Restful Partner', tester)
        
    @unittest.skipIf(not active_authentication, "Skipped because no authentication is available!")
    def test_write_multi(self):
        client = self.authenticate()
        ids = json.dumps([1, 2])
        values = json.dumps({'name': 'Restful Partner'})
        response = client.put(self.write_url, data={'model': 'res.partner', 'ids': ids, 'values': values})
        tester = self.env['res.partner'].browse([1, 2]).mapped('name')
        self.assertTrue(response)
        self.assertTrue(len(tester) == 2)
        self.assertTrue('Restful Partner' in tester)
    
    @unittest.skipIf(not active_authentication, "Skipped because no authentication is available!")
    def test_write_many2many(self):
        client = self.authenticate()
        ids = json.dumps([2])
        values = json.dumps({'name': 'Restful Partner', 'category_id': [[0, 0, {'name': 'Restful Category'}]]})
        response = client.put(self.write_url, data={'model': 'res.partner', 'ids': ids, 'values': values})
        tester = self.env['res.partner'].browse([2]).category_id.name
        self.assertTrue(response)
        self.assertEquals('Restful Category', tester)
    
    