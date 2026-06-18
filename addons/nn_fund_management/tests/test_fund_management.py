from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestFundManagement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.fund_user = new_test_user(
            cls.env,
            login='fund_user',
            groups='base.group_user,nn_fund_management.group_fund_user',
        )
        cls.finance_user = new_test_user(
            cls.env,
            login='finance_user',
            groups='base.group_user,nn_fund_management.group_finance_user',
        )
        cls.gm_user = new_test_user(
            cls.env,
            login='gm_user',
            groups='base.group_user,nn_fund_management.group_gm_approver',
        )
        cls.md_user = new_test_user(
            cls.env,
            login='md_user',
            groups='base.group_user,nn_fund_management.group_md_approver',
        )
        cls.account = cls.env['fund.account'].create({
            'name': 'Main Bank',
            'account_type': 'bank',
            'company_id': cls.company.id,
        })
        cls.project_a = cls.env['project.project'].create({
            'name': 'Project A',
            'company_id': cls.company.id,
        })
        cls.project_b = cls.env['project.project'].create({
            'name': 'Project B',
            'company_id': cls.company.id,
        })
        cls.salary = cls.env['fund.expense.head'].create({
            'name': 'Salary',
            'company_id': cls.company.id,
        })

    def _receive(self, amount=1000000, reference='TXN-001'):
        incoming = self.env['fund.incoming'].with_user(self.finance_user).create({
            'fund_account_id': self.account.id,
            'date': '2026-06-18',
            'amount': amount,
            'transaction_reference': reference,
            'sender': 'NN Services',
            'company_id': self.company.id,
        })
        incoming.action_confirm()
        return incoming

    def _approve(self, record):
        record.with_user(self.gm_user).action_approve()
        record.with_user(self.md_user).action_approve()

    def _allocate_project_a(self, amount=600000):
        allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'project_id': self.project_a.id,
            'amount': amount,
            'purpose': 'Project A funding',
            'company_id': self.company.id,
        })
        allocation.action_submit()
        self._approve(allocation)
        return allocation

    def test_incoming_funds_and_duplicate_reference(self):
        self._receive()
        self.assertEqual(self.account.available_unassigned_balance, 1000000)
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['fund.incoming'].with_user(self.finance_user).create({
                'fund_account_id': self.account.id,
                'date': '2026-06-18',
                'amount': 100,
                'transaction_reference': 'TXN-001',
                'sender': 'Duplicate',
                'company_id': self.company.id,
            })

    def test_demo_flow_blocks_double_spending(self):
        self._receive()
        allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'project_id': self.project_a.id,
            'amount': 600000,
            'purpose': 'Project A funding',
            'company_id': self.company.id,
        })
        allocation.action_submit()
        self.assertEqual(self.account.available_unassigned_balance, 400000)
        self.assertEqual(self.account.allocation_hold_amount, 600000)

        allocation.with_user(self.gm_user).action_reject()
        self.assertEqual(self.account.available_unassigned_balance, 1000000)

        allocation = self._allocate_project_a(600000)
        self.assertEqual(allocation.state, 'approved')
        self.assertEqual(self.project_a.fund_available, 600000)

        transfer = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_project_id': self.project_a.id,
            'destination_project_id': self.project_b.id,
            'amount': 200000,
            'reason': 'Move funds to Project B',
            'company_id': self.company.id,
        })
        transfer.action_submit()
        self.assertEqual(self.project_a.fund_available, 400000)
        self.assertEqual(self.project_a.fund_transfer_hold, 200000)
        self._approve(transfer)
        self.assertEqual(self.project_b.fund_available, 200000)

        requisition = self.env['fund.requisition'].with_user(self.fund_user).create({
            'project_id': self.project_b.id,
            'amount': 150000,
            'purpose': 'Project B vendor work',
            'company_id': self.company.id,
        })
        requisition.action_submit()
        self._approve(requisition)
        self.assertEqual(requisition.remaining_billable_amount, 150000)

        bill = self.env['fund.bill'].with_user(self.finance_user).create({
            'requisition_id': requisition.id,
            'project_id': self.project_b.id,
            'amount': 100000,
            'vendor': 'Vendor A',
            'company_id': self.company.id,
        })
        bill.action_post()
        self.assertEqual(requisition.remaining_billable_amount, 50000)

        with self.assertRaises(ValidationError):
            self.env['fund.bill'].with_user(self.finance_user).create({
                'requisition_id': requisition.id,
                'project_id': self.project_b.id,
                'amount': 60000,
                'vendor': 'Vendor B',
                'company_id': self.company.id,
            }).action_post()

        with self.assertRaises(ValidationError):
            self.env['fund.bill'].with_user(self.finance_user).create({
                'requisition_id': requisition.id,
                'project_id': self.project_a.id,
                'amount': 10000,
                'vendor': 'Wrong Project Vendor',
                'company_id': self.company.id,
            })

    def test_pending_transfer_money_cannot_be_requisitioned(self):
        self._receive()
        self._allocate_project_a(600000)
        transfer = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_project_id': self.project_a.id,
            'destination_project_id': self.project_b.id,
            'amount': 500000,
            'reason': 'Hold most funds',
            'company_id': self.company.id,
        })
        transfer.action_submit()
        with self.assertRaises(ValidationError):
            self.env['fund.requisition'].with_user(self.fund_user).create({
                'project_id': self.project_a.id,
                'amount': 200000,
                'purpose': 'Should be blocked',
                'company_id': self.company.id,
            }).action_submit()

    def test_md_cannot_approve_before_gm_and_self_approval_is_blocked(self):
        self._receive()
        allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'project_id': self.project_a.id,
            'amount': 100000,
            'purpose': 'Approval order',
            'company_id': self.company.id,
        })
        allocation.action_submit()
        with self.assertRaises(AccessError):
            allocation.with_user(self.md_user).action_approve()
        with self.assertRaises(AccessError):
            allocation.with_user(self.fund_user).action_approve()

    def test_bill_reversal_restores_remaining_amount(self):
        self._receive()
        self._allocate_project_a(200000)
        requisition = self.env['fund.requisition'].with_user(self.fund_user).create({
            'project_id': self.project_a.id,
            'amount': 100000,
            'purpose': 'Reversible spend',
            'company_id': self.company.id,
        })
        requisition.action_submit()
        self._approve(requisition)
        bill = self.env['fund.bill'].with_user(self.finance_user).create({
            'requisition_id': requisition.id,
            'project_id': self.project_a.id,
            'amount': 75000,
            'vendor': 'Vendor A',
            'company_id': self.company.id,
        })
        bill.action_post()
        self.assertEqual(requisition.remaining_billable_amount, 25000)
        bill.action_reverse()
        self.assertEqual(requisition.remaining_billable_amount, 100000)

    def test_bank_email_creates_pending_incoming_fund(self):
        email = self.env['fund.bank.email'].with_user(self.finance_user).create({
            'fund_account_id': self.account.id,
            'email_message_id': 'email-001',
            'bank_name': 'Demo Bank',
            'raw_body': 'Amount: BDT 25,000 Ref: BANK-TXN-001 Account: XXXX-1234 2026-06-18',
            'company_id': self.company.id,
        })
        email.action_parse()
        self.assertEqual(email.state, 'parsed')
        email.action_create_incoming()
        self.assertEqual(email.incoming_id.state, 'pending_verification')
        self.assertEqual(email.incoming_id.amount, 25000)
