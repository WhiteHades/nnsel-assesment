from odoo.exceptions import AccessError, UserError, ValidationError
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
        cls.utilities = cls.env['fund.expense.head'].create({
            'name': 'Utilities',
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

    def _allocate_expense(self, expense, amount=100000):
        allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'expense_head_id': expense.id,
            'amount': amount,
            'purpose': '%s funding' % expense.display_name,
            'company_id': self.company.id,
        })
        allocation.action_submit()
        self._approve(allocation)
        return allocation

    def test_target_scoped_approval_rules_block_unmatched_target_without_holding_money(self):
        self._receive()
        self.env['fund.approval.rule'].search([('request_type', '=', 'allocation')]).write({'active': False})
        self.env['fund.approval.rule'].create({
            'name': 'Salary GM approval',
            'request_type': 'allocation',
            'expense_head_id': self.salary.id,
            'sequence': 10,
            'approver_group_id': self.env.ref('nn_fund_management.group_gm_approver').id,
            'company_id': self.company.id,
        })
        self.env['fund.approval.rule'].create({
            'name': 'Salary MD approval',
            'request_type': 'allocation',
            'expense_head_id': self.salary.id,
            'sequence': 20,
            'approver_group_id': self.env.ref('nn_fund_management.group_md_approver').id,
            'company_id': self.company.id,
        })

        project_allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'project_id': self.project_a.id,
            'amount': 100000,
            'purpose': 'No matching target rule',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            project_allocation.action_submit()
        self.assertEqual(project_allocation.state, 'draft')
        self.assertEqual(self.account.available_unassigned_balance, 1000000)
        self.assertEqual(self.account.allocation_hold_amount, 0)

        salary_allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'expense_head_id': self.salary.id,
            'amount': 100000,
            'purpose': 'Salary funding',
            'company_id': self.company.id,
        })
        salary_allocation.action_submit()
        self.assertEqual(salary_allocation.state, 'submitted')
        self.assertEqual(salary_allocation.approval_step_ids.mapped('name'), ['Salary GM approval', 'Salary MD approval'])
        self.assertEqual(self.account.available_unassigned_balance, 900000)
        self.assertEqual(self.account.allocation_hold_amount, 100000)

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

    def test_incoming_security_repeated_confirm_and_unlink_are_server_side(self):
        incoming = self.env['fund.incoming'].with_user(self.finance_user).create({
            'fund_account_id': self.account.id,
            'date': '2026-06-18',
            'amount': 100000,
            'transaction_reference': 'SEC-001',
            'sender': 'NN Services',
            'company_id': self.company.id,
        })
        with self.assertRaises(AccessError):
            incoming.with_user(self.fund_user).action_confirm()
        incoming.with_user(self.finance_user).action_confirm()
        self.assertEqual(self.account.available_unassigned_balance, 100000)
        self.assertEqual(self.env['fund.movement'].search_count([
            ('source_model', '=', 'fund.incoming'),
            ('source_id', '=', incoming.id),
            ('purpose', '=', 'confirm'),
        ]), 1)
        with self.assertRaises(UserError):
            incoming.with_user(self.finance_user).action_confirm()
        self.assertEqual(self.env['fund.movement'].search_count([
            ('source_model', '=', 'fund.incoming'),
            ('source_id', '=', incoming.id),
            ('purpose', '=', 'confirm'),
        ]), 1)
        with self.assertRaises(UserError):
            incoming.unlink()
        history = self.env['fund.approval.history'].search([
            ('source_model', '=', 'fund.incoming'),
            ('source_id', '=', incoming.id),
            ('action', '=', 'approve'),
        ])
        self.assertEqual(history.new_state, 'confirmed')
        self.assertEqual(history.user_id, self.finance_user)

    def test_confirmed_incoming_cancel_reverses_unassigned_balance(self):
        incoming = self._receive(amount=250000, reference='CANCEL-001')
        with self.assertRaises(AccessError):
            incoming.with_user(self.fund_user).action_cancel()
        incoming.with_user(self.finance_user).action_cancel()
        self.assertEqual(incoming.state, 'cancelled')
        self.assertEqual(self.account.available_unassigned_balance, 0)
        self.assertEqual(self.env['fund.movement'].search_count([
            ('source_model', '=', 'fund.incoming'),
            ('source_id', '=', incoming.id),
            ('purpose', '=', 'cancel'),
        ]), 1)

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

    def test_expense_head_requisition_billing_and_wrong_head_are_controlled(self):
        self._receive()
        self._allocate_expense(self.salary, 300000)
        requisition = self.env['fund.requisition'].with_user(self.fund_user).create({
            'expense_head_id': self.salary.id,
            'amount': 150000,
            'purpose': 'Salary vendor work',
            'company_id': self.company.id,
        })
        requisition.action_submit()
        self._approve(requisition)
        bill = self.env['fund.bill'].with_user(self.finance_user).create({
            'requisition_id': requisition.id,
            'expense_head_id': self.salary.id,
            'amount': 100000,
            'vendor': 'Salary Vendor',
            'company_id': self.company.id,
        })
        bill.action_post()
        self.assertEqual(requisition.remaining_billable_amount, 50000)
        self.assertEqual(self.salary.total_spent_amount, 100000)
        with self.assertRaises(ValidationError):
            self.env['fund.bill'].with_user(self.finance_user).create({
                'requisition_id': requisition.id,
                'expense_head_id': self.utilities.id,
                'amount': 10000,
                'vendor': 'Wrong Head Vendor',
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

    def test_requisition_close_releases_unused_amount(self):
        self._receive()
        self._allocate_project_a(200000)
        requisition = self.env['fund.requisition'].with_user(self.fund_user).create({
            'project_id': self.project_a.id,
            'amount': 100000,
            'purpose': 'Close with unused money',
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
        requisition.action_close()
        self.assertEqual(requisition.state, 'closed')
        self.assertEqual(requisition.remaining_billable_amount, 0)
        self.assertEqual(requisition.released_amount, 25000)
        self.assertEqual(self.project_a.fund_available, 125000)
        self.assertEqual(self.project_a.fund_approved_unspent, 0)

    def test_transfer_variants_and_held_money_cannot_transfer_again(self):
        self._receive()
        self._allocate_project_a(500000)
        self._allocate_expense(self.salary, 300000)

        pending = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_project_id': self.project_a.id,
            'destination_project_id': self.project_b.id,
            'amount': 200000,
            'reason': 'Hold Project A funds',
            'company_id': self.company.id,
        })
        pending.action_submit()
        self.assertEqual(self.project_a.fund_transfer_hold, 200000)
        with self.assertRaises(ValidationError):
            self.env['fund.transfer'].with_user(self.fund_user).create({
                'source_project_id': self.project_a.id,
                'destination_expense_head_id': self.salary.id,
                'amount': 350000,
                'reason': 'Cannot reuse held money',
                'company_id': self.company.id,
            }).action_submit()
        self._approve(pending)
        self.assertEqual(self.project_b.fund_available, 200000)

        project_to_expense = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_project_id': self.project_a.id,
            'destination_expense_head_id': self.salary.id,
            'amount': 100000,
            'reason': 'Project to salary',
            'company_id': self.company.id,
        })
        project_to_expense.action_submit()
        self._approve(project_to_expense)

        expense_to_project = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_expense_head_id': self.salary.id,
            'destination_project_id': self.project_b.id,
            'amount': 50000,
            'reason': 'Salary to Project B',
            'company_id': self.company.id,
        })
        expense_to_project.action_submit()
        self._approve(expense_to_project)

        expense_to_expense = self.env['fund.transfer'].with_user(self.fund_user).create({
            'source_expense_head_id': self.salary.id,
            'destination_expense_head_id': self.utilities.id,
            'amount': 50000,
            'reason': 'Salary to utilities',
            'company_id': self.company.id,
        })
        expense_to_expense.action_submit()
        self._approve(expense_to_expense)

        self.assertEqual(self.project_a.fund_available, 200000)
        self.assertEqual(self.project_b.fund_available, 250000)
        self.assertEqual(self.salary.available_fund, 300000)
        self.assertEqual(self.utilities.available_fund, 50000)
        with self.assertRaises(ValidationError):
            self.env['fund.transfer'].with_user(self.fund_user).create({
                'source_project_id': self.project_a.id,
                'destination_project_id': self.project_a.id,
                'amount': 1000,
                'reason': 'Same target',
                'company_id': self.company.id,
            })

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

    def test_bank_email_failure_and_duplicate_email_are_controlled(self):
        email = self.env['fund.bank.email'].with_user(self.finance_user).create({
            'fund_account_id': self.account.id,
            'email_message_id': 'email-failed-001',
            'bank_name': 'Demo Bank',
            'raw_body': 'No transaction data in this message',
            'company_id': self.company.id,
        })
        email.action_parse()
        self.assertEqual(email.state, 'failed')
        self.assertTrue(email.parse_error)
        self.assertEqual(email.activity_ids[:1].summary, 'Bank email parsing failed')
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['fund.bank.email'].with_user(self.finance_user).create({
                'fund_account_id': self.account.id,
                'email_message_id': 'email-failed-001',
                'bank_name': 'Demo Bank',
                'raw_body': 'Amount: BDT 10 Ref: DUP-001',
                'company_id': self.company.id,
            })

    def test_dashboard_summarizes_balances_and_pending_approvals(self):
        self._receive()
        allocation = self.env['fund.allocation'].with_user(self.fund_user).create({
            'fund_account_id': self.account.id,
            'project_id': self.project_a.id,
            'amount': 600000,
            'purpose': 'Dashboard funding',
            'company_id': self.company.id,
        })
        allocation.action_submit()
        dashboard = self.env.ref('nn_fund_management.fund_dashboard_main')
        self.assertEqual(dashboard.total_received, 1000000)
        self.assertEqual(dashboard.unassigned_balance, 400000)
        self.assertEqual(dashboard.held_amount, 600000)
        self.assertEqual(dashboard.pending_approval_count, 2)
        self.assertTrue(dashboard.recent_movement_ids)
