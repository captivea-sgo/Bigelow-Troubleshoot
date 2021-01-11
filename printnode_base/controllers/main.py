# Copyright 2019 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json

from odoo.addons.web.controllers.main import DataSet, ReportController

from odoo.http import request
from odoo.http import serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.tools.translate import _
from odoo import http
from werkzeug.exceptions import ImATeapot

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'
PDF = ['qweb-pdf']
RAW = ['qweb-text']


# we use this dummy exception to clearly differenciate
# printnode exception in ajax response for downloading report
class PrintNodeSuccess(ImATeapot):
    pass


class ControllerProxy(http.Controller):

    def printnode_print(self, printer_id,
                        report_id=None, objects=None,
                        response=None):
        """ PrintNode
        """
        if report_id and objects:
            ret = printer_id.printnode_print(report_id, objects) #render
        elif response:
            ret = printer_id.printnode_print_b64(response.data, {
                'title': response.headers.get('Content-Disposition', ''),
                'pdf': False,
                'copies': 1,
            })
        else:
            ret = None

class DataSetProxy(DataSet, ControllerProxy):

    @http.route('/web/dataset/call_button', type='json', auth="user")
    def call_button(self, model, method, args, domain_id=None, context_id=None):
        """ print reports on call_button
        """

        if not request.env.user.has_group(SECURITY_GROUP) \
                or not request.env.user.company_id.printnode_enabled \
                or not request.env.user.printnode_enabled:
            return super(DataSetProxy, self).\
                call_button(model, method, args, domain_id, context_id)

        printnode_action = request.env['printnode.action.button']

        actions = printnode_action.search([
            ('model_id.model', '=', model),
            ('method_id.method', '=', method),
        ])

        # removed: automatically create missed printnode.action.button(s)

        objects = request.env[model].browse(args[0][0])
        post, pre = [], []

        for action in actions.filtered(
                lambda a: a.active and a.report_id and a.printer_id):
            (post, pre)[action.preprint].append(action)

        for action in pre:
            super(DataSetProxy, self).\
                printnode_print(action.printer_id,
                                report_id=action.report_id,
                                objects=objects)

        result = super(DataSetProxy, self).\
            call_button(model, method, args, domain_id, context_id)

        for action in post:
            super(DataSetProxy, self).\
                printnode_print(action.printer_id,
                                report_id=action.report_id,
                                objects=objects)

        return result


class ReportControllerProxy(ReportController, ControllerProxy):

    @http.route('/report/download', type='http', auth="user")
    def report_download(self, data, token):
        """ print reports on report_download
        """

        if not request.env.user.has_group(SECURITY_GROUP) \
                or not request.env.user.company_id.printnode_enabled \
                or not request.env.user.printnode_enabled:
            return super(ReportControllerProxy, self).\
                report_download(data, token)

        requestcontent = json.loads(data)

        # if requestcontent[1] not in PDF + RAW:
        #     return super(ReportControllerProxy, self).\
        #         report_download(data, token)

        ext = requestcontent[1].split('-')[1]

        report, object_ids = requestcontent[0].\
            split('/report/{}/'.format(ext))[1].split('?')[0].split('/')
        report_id = request.env['ir.actions.report'].\
            _get_report_from_name(report)

        printnode_rules = request.env['printnode.rule']

        rule = printnode_rules.search([
            ('user_id', '=', request.env.user.id),
            ('report_id', '=', report_id.id),
        ])

        printer_id = len(rule) == 1 and rule.printer_id \
            or request.env.user.printnode_printer \
            or request.env.user.company_id.printnode_printer

        if not printer_id:
            return super(ReportControllerProxy, self).\
                report_download(data, token)

        try:
            if requestcontent[1] in PDF:

                ids = [int(x) for x in object_ids.split(',')]
                obj = request.env[report_id.model].browse(ids)

                super(ReportControllerProxy, self).\
                    printnode_print(printer_id, report_id, obj)

            if requestcontent[1] in RAW:

                response = super(ReportControllerProxy, self).\
                    report_download(data, token)

                super(ReportControllerProxy, self).\
                    printnode_print(printer_id, response=response)

        except Exception as e:
            return request.make_response(html_escape(json.dumps({
                'code': 200,
                'message': "Odoo Server Error",
                'data': _serialize_exception(e)
            })))

        raise PrintNodeSuccess(_('Sent to PrintNode'))
