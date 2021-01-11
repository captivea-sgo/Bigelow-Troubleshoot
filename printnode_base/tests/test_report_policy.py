# Copyright 2019 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo.exceptions import UserError
from odoo.tests import common
from unittest.mock import patch

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class TestPrintNodeReport(common.TransactionCase):

    def setUp(self):
        super(TestPrintNodeReport, self).setUp()

        self.company = self.env.ref('base.main_company')

        self.user = self.env['res.users'].with_context({
            'no_reset_password': True
        }).create({
            'name': 'Printnode User',
            'company_id': self.company.id,
            'login': 'user',
            'email': 'user@print.node',
            'groups_id': [(6, 0, [
                self.env.ref(SECURITY_GROUP).id
            ])]
        })

        # report

        self.report = self.env['ir.actions.report'].create({
            'name': 'Model Overview',
            'model': 'ir.model',
            'report_type': 'qweb-pdf',
            'report_name': 'base.report_irmodeloverview'
        })

        # device

        self.account = self.env['printnode.account'].create({
            'username': 'apikey'
        })

        self.computer = self.env['printnode.computer'].create({
            'name': 'Local Computer',
            'status': 'connected',
            'account_id': self.account.id,
        })

        self.printer = self.env['printnode.printer'].create({
            'name': 'Local Printer',
            'status': 'offline',
            'computer_id': self.computer.id,
        })

        self.policy = self.env['printnode.report.policy'].create({
            'printer_id': self.printer.id,
            'report_id': self.report.id,
        })

    def test_printnode_module_disabled(self):
        self.company.printnode_enabled = False

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_and_raise()

    def test_printnode_recheck(self):
        self.company.printnode_enabled = True
        self.company.printnode_recheck = True

        with self.assertRaises(UserError), self.cr.savepoint(), \
                patch.object(self.account, 'recheck_printer', return_value=False) as _:
            self.printer.with_context(user=self.user).printnode_check_and_raise()

    def test_printnode_no_recheck(self):
        self.company.printnode_enabled = True
        self.company.printnode_recheck = False

        self.printer.with_context(user=self.user).printnode_check_and_raise()

    def test_printnode_policy_report_no_size_and_printer_no_size(self):
        self.company.printnode_enabled = True

        self.policy.report_paper_id = None
        self.printer.paper_ids = [(5, 0, 0)]

        self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_no_size_and_printer_size(self):
        self.company.printnode_enabled = True

        self.policy.report_paper_id = None
        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a4').id])]

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_size_and_printer_no_size(self):
        self.company.printnode_enabled = True

        self.policy.report_paper_id = \
            self.env.ref('printnode_base.printnode_paper_a6')
        self.printer.paper_ids = [(5, 0, 0)]

        self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_size_not_eq_printer_size(self):
        self.company.printnode_enabled = True

        self.policy.report_paper_id = \
            self.env.ref('printnode_base.printnode_paper_a6')
        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a4').id])]

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_size_eq_printer_size(self):
        self.company.printnode_enabled = True

        self.policy.report_paper_id = \
            self.env.ref('printnode_base.printnode_paper_a6')
        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a6').id])]

        self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_type_and_printer_no_type(self):
        self.company.printnode_enabled = True

        self.policy.report_type = 'qweb-pdf'
        self.printer.format_ids = [(5, 0, 0)]

        self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_type_not_eq_printer_type(self):
        self.company.printnode_enabled = True

        self.policy.report_type = 'qweb-pdf'
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_raw').id])]

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_report_type_eq_printer_type(self):
        self.company.printnode_enabled = True

        self.policy.report_type = 'qweb-pdf'
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_pdf').id])]

        self.printer.with_context(user=self.user).printnode_check_report(self.report)

    def test_printnode_policy_attachment_wrong_type(self):
        self.company.printnode_enabled = True

        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a4').id])]
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_raw').id])]

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_and_raise({
                'title': 'Label',
                'type': 'qweb-pdf',
                'size': self.env.ref('printnode_base.printnode_paper_a4'),
            })

    def test_printnode_policy_attachment_wrong_size(self):
        self.company.printnode_enabled = True

        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a6').id])]
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_pdf').id])]

        with self.assertRaises(UserError), self.cr.savepoint():
            self.printer.with_context(user=self.user).printnode_check_and_raise({
                'title': 'Label',
                'type': 'qweb-pdf',
                'size': self.env.ref('printnode_base.printnode_paper_a4'),
            })

    def test_printnode_policy_attachment_empty_params(self):
        self.company.printnode_enabled = True

        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a4').id])]
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_pdf').id])]

        self.printer.with_context(user=self.user).printnode_check_and_raise({
            'title': 'Label',
        })

    def test_printnode_policy_attachment_valid_params(self):
        self.company.printnode_enabled = True

        self.printer.paper_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_paper_a4').id])]
        self.printer.format_ids = [(6, 0, [
            self.env.ref('printnode_base.printnode_content_type_pdf').id])]

        self.printer.with_context(user=self.user).printnode_check_and_raise({
            'title': 'Label',
            'type': 'qweb-pdf',
            'size': self.env.ref('printnode_base.printnode_paper_a4'),
        })
