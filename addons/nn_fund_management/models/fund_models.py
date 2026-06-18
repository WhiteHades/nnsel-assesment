import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


TARGET_BUCKETS = {
    'available': 'target_available',
    'requisition_hold': 'target_requisition_hold',
    'transfer_hold': 'target_transfer_hold',
    'reserved': 'target_reserved',
    'spent': 'target_spent',
}


class FundMovement(models.Model):
    _name = 'fund.movement'
    _description = 'Fund Movement'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(required=True, default=lambda self: _('New'), copy=False)
    movement_key = fields.Char(required=True, copy=False, index=True)
    source_model = fields.Char(required=True, copy=False, index=True)
    source_id = fields.Integer(required=True, copy=False, index=True)
    purpose = fields.Char(required=True, copy=False, index=True)
    movement_type = fields.Selection([
        ('incoming_confirm', 'Incoming confirmation'),
        ('incoming_cancel', 'Incoming cancellation'),
        ('allocation_submit', 'Allocation hold'),
        ('allocation_approve', 'Allocation approval'),
        ('allocation_release', 'Allocation release'),
        ('requisition_submit', 'Requisition hold'),
        ('requisition_approve', 'Requisition approval'),
        ('requisition_release', 'Requisition release'),
        ('bill_post', 'Bill posting'),
        ('bill_reverse', 'Bill reversal'),
        ('transfer_submit', 'Transfer hold'),
        ('transfer_approve', 'Transfer approval'),
        ('transfer_release', 'Transfer release'),
    ], required=True, index=True)
    bucket = fields.Selection([
        ('account_unassigned', 'Account unassigned'),
        ('account_allocation_hold', 'Account allocation hold'),
        ('target_available', 'Target available'),
        ('target_requisition_hold', 'Target requisition hold'),
        ('target_transfer_hold', 'Target transfer hold'),
        ('target_reserved', 'Approved but unspent'),
        ('target_spent', 'Spent'),
    ], required=True, index=True)
    direction = fields.Selection([
        ('in', 'In'),
        ('out', 'Out'),
    ], required=True, index=True)
    amount = fields.Monetary(required=True, currency_field='currency_id')
    signed_amount = fields.Monetary(compute='_compute_signed_amount', currency_field='currency_id', store=True)
    fund_account_id = fields.Many2one('fund.account', string='Fund Account', index=True, ondelete='restrict')
    project_id = fields.Many2one('project.project', string='Project', index=True, ondelete='restrict', check_company=True)
    expense_head_id = fields.Many2one('fund.expense.head', string='Expense Head', index=True, ondelete='restrict', check_company=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    description = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)

    _movement_key_unique = models.Constraint(
        'unique(movement_key)',
        'This fund movement was already recorded.',
    )
    _movement_amount_positive = models.Constraint(
        'check(amount > 0)',
        'Movement amount must be positive.',
    )

    @api.depends('amount', 'direction')
    def _compute_signed_amount(self):
        for movement in self:
            movement.signed_amount = movement.amount if movement.direction == 'in' else -movement.amount

    @api.constrains('fund_account_id', 'project_id', 'expense_head_id')
    def _check_single_target(self):
        for movement in self:
            targets = sum(bool(value) for value in (
                movement.fund_account_id,
                movement.project_id,
                movement.expense_head_id,
            ))
            if targets != 1:
                raise ValidationError(_('A fund movement must reference exactly one fund account, project, or expense head.'))

    def unlink(self):
        raise UserError(_('Fund movements are audit records and cannot be deleted.'))


class FundApprovalRule(models.Model):
    _name = 'fund.approval.rule'
    _description = 'Fund Approval Rule'
    _order = 'request_type, sequence, min_amount, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    request_type = fields.Selection([
        ('allocation', 'Allocation'),
        ('requisition', 'Requisition'),
        ('transfer', 'Transfer'),
    ], required=True, index=True)
    min_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    max_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    project_id = fields.Many2one('project.project', check_company=True)
    expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    sequence = fields.Integer(default=10, required=True)
    approver_user_id = fields.Many2one('res.users', string='Approver User')
    approver_group_id = fields.Many2one('res.groups', string='Approver Group')

    @api.constrains('approver_user_id', 'approver_group_id')
    def _check_approver(self):
        for rule in self:
            if bool(rule.approver_user_id) == bool(rule.approver_group_id):
                raise ValidationError(_('Set either an approver user or an approver group.'))

    @api.constrains('min_amount', 'max_amount')
    def _check_amount_range(self):
        for rule in self:
            if rule.min_amount < 0 or rule.max_amount < 0:
                raise ValidationError(_('Approval rule amounts cannot be negative.'))
            if rule.max_amount and rule.max_amount < rule.min_amount:
                raise ValidationError(_('Maximum amount cannot be below minimum amount.'))

    @api.constrains('project_id', 'expense_head_id')
    def _check_single_target(self):
        for rule in self:
            if rule.project_id and rule.expense_head_id:
                raise ValidationError(_('Set either a project or an expense head, not both.'))

    @api.model
    def matching_rules(self, request_type, amount, company, project=None, expense=None):
        domain = [
            ('active', '=', True),
            ('request_type', '=', request_type),
            '|', ('company_id', '=', False), ('company_id', '=', company.id),
            ('min_amount', '<=', amount),
            '|', ('max_amount', 'in', [False, 0.0]), ('max_amount', '>=', amount),
        ]
        if project:
            domain.extend(['|', '&', ('project_id', '=', False), ('expense_head_id', '=', False), ('project_id', '=', project.id)])
        elif expense:
            domain.extend(['|', '&', ('project_id', '=', False), ('expense_head_id', '=', False), ('expense_head_id', '=', expense.id)])
        else:
            domain.extend([('project_id', '=', False), ('expense_head_id', '=', False)])
        rules = self.search(domain)
        if not rules:
            raise UserError(_('No approval rule is configured for this request.'))
        return rules.sorted(lambda rule: (rule.sequence, rule.id))


class FundApprovalStep(models.Model):
    _name = 'fund.approval.step'
    _description = 'Fund Approval Step'
    _order = 'source_model, source_id, sequence, id'

    name = fields.Char(required=True)
    source_model = fields.Char(required=True, index=True)
    source_id = fields.Integer(required=True, index=True)
    allocation_id = fields.Many2one('fund.allocation', ondelete='cascade')
    requisition_id = fields.Many2one('fund.requisition', ondelete='cascade')
    transfer_id = fields.Many2one('fund.transfer', ondelete='cascade')
    rule_id = fields.Many2one('fund.approval.rule', ondelete='restrict')
    sequence = fields.Integer(required=True)
    approver_user_id = fields.Many2one('res.users')
    approver_group_id = fields.Many2one('res.groups')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', required=True, index=True)
    decision_user_id = fields.Many2one('res.users')
    decision_date = fields.Datetime()
    comment = fields.Text()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)

    def can_user_approve(self, user):
        self.ensure_one()
        return self.approver_user_id == user or (
            self.approver_group_id and self.approver_group_id in user.all_group_ids
        )


class FundApprovalHistory(models.Model):
    _name = 'fund.approval.history'
    _description = 'Fund Approval History'
    _order = 'date desc, id desc'

    source_model = fields.Char(required=True, index=True)
    source_id = fields.Integer(required=True, index=True)
    allocation_id = fields.Many2one('fund.allocation', ondelete='cascade')
    requisition_id = fields.Many2one('fund.requisition', ondelete='cascade')
    transfer_id = fields.Many2one('fund.transfer', ondelete='cascade')
    action = fields.Selection([
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
        ('close', 'Closed'),
        ('post', 'Posted'),
        ('reverse', 'Reversed'),
        ('release', 'Released'),
    ], required=True)
    previous_state = fields.Char()
    new_state = fields.Char()
    approval_level = fields.Char()
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    comment = fields.Text()
    amount = fields.Monetary(currency_field='currency_id')
    fund_account_id = fields.Many2one('fund.account')
    project_id = fields.Many2one('project.project')
    expense_head_id = fields.Many2one('fund.expense.head')
    reference = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)


class FundRequestMixin(models.AbstractModel):
    _name = 'fund.request.mixin'
    _description = 'Fund Request Mixin'

    def _is_admin(self):
        return self.env.user.has_group('nn_fund_management.group_fund_administrator')

    def _is_finance(self):
        return self.env.user.has_group('nn_fund_management.group_finance_user') or self._is_admin()

    def _check_group(self, xmlid, message):
        if not (self.env.user.has_group(xmlid) or self._is_admin()):
            raise AccessError(message)

    def _check_positive_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be positive.'))

    def _lock_target_scope(self, project=None, expense=None):
        if project:
            self.env.cr.execute('SELECT id FROM project_project WHERE id = ANY(%s) FOR UPDATE', [project.ids])
        if expense:
            self.env.cr.execute('SELECT id FROM fund_expense_head WHERE id = ANY(%s) FOR UPDATE', [expense.ids])

    def _movement_exists(self, purpose):
        self.ensure_one()
        return bool(self.env['fund.movement'].search_count([
            ('source_model', '=', self._name),
            ('source_id', '=', self.id),
            ('purpose', '=', purpose),
        ]))

    def _create_movement(self, purpose, movement_type, bucket, direction, amount, description=None, fund_account=None, project=None, expense_head=None):
        self.ensure_one()
        key = '%s:%s:%s:%s:%s' % (self._name, self.id, purpose, bucket, direction)
        movement_model = self.env['fund.movement'].sudo()
        existing = movement_model.search([('movement_key', '=', key)], limit=1)
        if existing:
            return existing
        return movement_model.create({
            'name': self.display_name,
            'movement_key': key,
            'source_model': self._name,
            'source_id': self.id,
            'purpose': purpose,
            'movement_type': movement_type,
            'bucket': bucket,
            'direction': direction,
            'amount': amount,
            'fund_account_id': fund_account.id if fund_account else False,
            'project_id': project.id if project else False,
            'expense_head_id': expense_head.id if expense_head else False,
            'description': description,
            'company_id': self.company_id.id,
        })

    def _target_values(self, prefix=''):
        self.ensure_one()
        project = self[prefix + 'project_id'] if prefix + 'project_id' in self._fields else self.project_id
        expense = self[prefix + 'expense_head_id'] if prefix + 'expense_head_id' in self._fields else self.expense_head_id
        return project, expense

    def _target_label(self, project=None, expense=None):
        self.ensure_one()
        project = project if project is not None else self.project_id
        expense = expense if expense is not None else self.expense_head_id
        return project.display_name if project else expense.display_name

    def _target_balance(self, bucket_name, project=None, expense=None):
        self.ensure_one()
        bucket = TARGET_BUCKETS[bucket_name]
        domain = [
            ('bucket', '=', bucket),
            ('company_id', '=', self.company_id.id),
        ]
        if project:
            domain.append(('project_id', '=', project.id))
        elif expense:
            domain.append(('expense_head_id', '=', expense.id))
        else:
            raise ValidationError(_('A project or expense head is required.'))
        movements = self.env['fund.movement']._read_group(domain, [], ['signed_amount:sum'])
        return movements[0][0] if movements else 0.0

    def _create_target_movement(self, purpose, movement_type, bucket_name, direction, amount, project=None, expense=None, description=None):
        self.ensure_one()
        project = project if project is not None else self.project_id
        expense = expense if expense is not None else self.expense_head_id
        return self._create_movement(
            purpose=purpose,
            movement_type=movement_type,
            bucket=TARGET_BUCKETS[bucket_name],
            direction=direction,
            amount=amount,
            project=project,
            expense_head=expense,
            description=description,
        )

    def _history(self, action, previous_state, new_state, comment=None, approval_level=None, amount=None, fund_account=None, project=None, expense_head=None):
        self.ensure_one()
        vals = {
            'source_model': self._name,
            'source_id': self.id,
            'action': action,
            'previous_state': previous_state,
            'new_state': new_state,
            'approval_level': approval_level,
            'comment': comment,
            'amount': amount if amount is not None else getattr(self, 'amount', 0.0),
            'fund_account_id': fund_account.id if fund_account else getattr(self, 'fund_account_id', False).id if 'fund_account_id' in self._fields and self.fund_account_id else False,
            'project_id': project.id if project else getattr(self, 'project_id', False).id if 'project_id' in self._fields and self.project_id else False,
            'expense_head_id': expense_head.id if expense_head else getattr(self, 'expense_head_id', False).id if 'expense_head_id' in self._fields and self.expense_head_id else False,
            'reference': self.display_name,
            'company_id': self.company_id.id,
        }
        if self._name == 'fund.allocation':
            vals['allocation_id'] = self.id
        elif self._name == 'fund.requisition':
            vals['requisition_id'] = self.id
        elif self._name == 'fund.transfer':
            vals['transfer_id'] = self.id
        self.env['fund.approval.history'].sudo().create(vals)

    def _approval_steps(self):
        self.ensure_one()
        return self.env['fund.approval.step'].search([
            ('source_model', '=', self._name),
            ('source_id', '=', self.id),
        ])

    def _approval_rule_target(self):
        self.ensure_one()
        if self._name == 'fund.transfer':
            return self._source()
        if 'project_id' in self._fields and 'expense_head_id' in self._fields:
            return self._target_values()
        return False, False

    def _matching_approval_rules(self, request_type):
        self.ensure_one()
        project, expense = self._approval_rule_target()
        return self.env['fund.approval.rule'].matching_rules(
            request_type,
            self.amount,
            self.company_id,
            project=project,
            expense=expense,
        )

    def _pending_step(self):
        self.ensure_one()
        return self._approval_steps().filtered(lambda step: step.state == 'pending')[:1]

    def _create_approval_steps(self, request_type, rules=None):
        self.ensure_one()
        if self._approval_steps():
            return
        rules = rules or self._matching_approval_rules(request_type)
        for rule in rules:
            vals = {
                'name': rule.name,
                'source_model': self._name,
                'source_id': self.id,
                'rule_id': rule.id,
                'sequence': rule.sequence,
                'approver_user_id': rule.approver_user_id.id,
                'approver_group_id': rule.approver_group_id.id,
                'company_id': self.company_id.id,
            }
            if self._name == 'fund.allocation':
                vals['allocation_id'] = self.id
            elif self._name == 'fund.requisition':
                vals['requisition_id'] = self.id
            elif self._name == 'fund.transfer':
                vals['transfer_id'] = self.id
            self.env['fund.approval.step'].sudo().create(vals)
        self._schedule_current_approver_activity()

    def _schedule_current_approver_activity(self):
        self.ensure_one()
        if not hasattr(self, 'activity_schedule'):
            return
        step = self._pending_step()
        if not step:
            return
        users = step.approver_user_id
        if not users and step.approver_group_id:
            users = self.env['res.users'].sudo().search([
                ('active', '=', True),
                ('all_group_ids', 'in', step.approver_group_id.ids),
            ], limit=1)
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_('Approval required'),
                note=_('Please review %s.') % self.display_name,
            )

    def _check_current_approver(self, step):
        self.ensure_one()
        if not step:
            raise UserError(_('No approval step is pending.'))
        if not step.can_user_approve(self.env.user):
            raise AccessError(_('Only the current approver can approve or reject this request.'))
        if getattr(self, 'requested_by_id', False) == self.env.user and not self.env.user.has_group('nn_fund_management.group_self_approval_override'):
            raise AccessError(_('You cannot approve your own request.'))

    def _approve_step(self, comment=None):
        self.ensure_one()
        step = self._pending_step()
        self._check_current_approver(step)
        step.sudo().write({
            'state': 'approved',
            'decision_user_id': self.env.user.id,
            'decision_date': fields.Datetime.now(),
            'comment': comment,
        })
        self._history('approve', self.state, self.state, comment=comment, approval_level=step.name)
        self.message_post(body=_('%s approved by %s.') % (step.name, self.env.user.display_name))
        self.activity_unlink(['mail.mail_activity_data_todo'])
        return step

    def _reject_step(self, comment=None):
        self.ensure_one()
        step = self._pending_step()
        self._check_current_approver(step)
        step.sudo().write({
            'state': 'rejected',
            'decision_user_id': self.env.user.id,
            'decision_date': fields.Datetime.now(),
            'comment': comment,
        })
        previous = self.state
        self.write({'state': 'rejected'})
        self._history('reject', previous, 'rejected', comment=comment, approval_level=step.name)
        self.message_post(body=_('%s rejected by %s.') % (step.name, self.env.user.display_name))
        self.activity_unlink(['mail.mail_activity_data_todo'])


class FundAccount(models.Model):
    _name = 'fund.account'
    _description = 'Fund Account'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    account_type = fields.Selection([
        ('bank', 'Bank'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ], required=True, default='bank', tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    movement_ids = fields.One2many('fund.movement', 'fund_account_id')
    total_received = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    available_unassigned_balance = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    allocation_hold_amount = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    total_assigned_amount = fields.Monetary(compute='_compute_balances', currency_field='currency_id')

    @api.depends('movement_ids.signed_amount', 'movement_ids.bucket')
    def _compute_balances(self):
        grouped = self.env['fund.movement']._read_group(
            [('fund_account_id', 'in', self.ids)],
            ['fund_account_id', 'bucket'],
            ['signed_amount:sum'],
        )
        totals = {}
        for account, bucket, signed_amount_sum in grouped:
            totals.setdefault(account.id, {})[bucket] = signed_amount_sum
        incoming_totals = {
            account.id: amount_sum
            for account, amount_sum in self.env['fund.movement']._read_group([
                ('fund_account_id', 'in', self.ids),
                ('movement_type', '=', 'incoming_confirm'),
            ], ['fund_account_id'], ['amount:sum'])
        }
        assigned_totals = {
            account.id: amount_sum
            for account, amount_sum in self.env['fund.allocation']._read_group([
                ('fund_account_id', 'in', self.ids),
                ('state', '=', 'approved'),
            ], ['fund_account_id'], ['amount:sum'])
        }
        for account in self:
            values = totals.get(account.id, {})
            account.total_received = incoming_totals.get(account.id, 0.0)
            account.available_unassigned_balance = values.get('account_unassigned', 0.0)
            account.allocation_hold_amount = values.get('account_allocation_hold', 0.0)
            account.total_assigned_amount = assigned_totals.get(account.id, 0.0)

    def _lock_company_scope(self):
        if self.ids:
            self.env.cr.execute('SELECT id FROM fund_account WHERE id = ANY(%s) FOR UPDATE', [self.ids])


class FundExpenseHead(models.Model):
    _name = 'fund.expense.head'
    _description = 'Fund Expense Head'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    movement_ids = fields.One2many('fund.movement', 'expense_head_id')
    total_allocated_fund = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    available_fund = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    requisition_hold = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    transfer_hold = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    approved_unspent_amount = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    total_spent_amount = fields.Monetary(compute='_compute_balances', currency_field='currency_id')
    incoming_transfer_amount = fields.Monetary(compute='_compute_transfer_totals', currency_field='currency_id')
    outgoing_transfer_amount = fields.Monetary(compute='_compute_transfer_totals', currency_field='currency_id')

    @api.depends('movement_ids.signed_amount', 'movement_ids.bucket')
    def _compute_balances(self):
        grouped = self.env['fund.movement']._read_group(
            [('expense_head_id', 'in', self.ids)],
            ['expense_head_id', 'bucket'],
            ['signed_amount:sum'],
        )
        totals = {}
        for head, bucket, signed_amount_sum in grouped:
            totals.setdefault(head.id, {})[bucket] = signed_amount_sum
        for head in self:
            values = totals.get(head.id, {})
            head.available_fund = values.get('target_available', 0.0)
            head.requisition_hold = values.get('target_requisition_hold', 0.0)
            head.transfer_hold = values.get('target_transfer_hold', 0.0)
            head.approved_unspent_amount = values.get('target_reserved', 0.0)
            head.total_spent_amount = values.get('target_spent', 0.0)
            head.total_allocated_fund = head.available_fund + head.requisition_hold + head.transfer_hold + head.approved_unspent_amount + head.total_spent_amount

    def _compute_transfer_totals(self):
        for head in self:
            incoming = self.env['fund.movement']._read_group([
                ('expense_head_id', '=', head.id),
                ('movement_type', '=', 'transfer_approve'),
                ('bucket', '=', 'target_available'),
                ('direction', '=', 'in'),
            ], [], ['amount:sum'])
            outgoing = self.env['fund.movement']._read_group([
                ('expense_head_id', '=', head.id),
                ('movement_type', '=', 'transfer_submit'),
                ('bucket', '=', 'target_transfer_hold'),
                ('direction', '=', 'in'),
            ], [], ['amount:sum'])
            head.incoming_transfer_amount = incoming[0][0] if incoming else 0.0
            head.outgoing_transfer_amount = outgoing[0][0] if outgoing else 0.0


class FundIncoming(models.Model):
    _name = 'fund.incoming'
    _description = 'Incoming Fund'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fund.request.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'), tracking=True)
    fund_account_id = fields.Many2one('fund.account', required=True, tracking=True, check_company=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    amount = fields.Monetary(required=True, currency_field='currency_id', tracking=True)
    transaction_reference = fields.Char(required=True, tracking=True)
    sender = fields.Char(string='Sender or Source', tracking=True)
    description = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_verification', 'Pending Verification'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)

    _fund_reference_unique = models.Constraint(
        'unique(fund_account_id, transaction_reference)',
        'The same transaction reference cannot be used twice within one fund account.',
    )
    _incoming_amount_positive = models.Constraint(
        'check(amount > 0)',
        'Incoming fund amount must be positive.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('fund.incoming') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        self._check_group('nn_fund_management.group_finance_user', _('Only finance users can confirm incoming funds.'))
        for incoming in self:
            if incoming.state not in ('draft', 'pending_verification'):
                raise UserError(_('Only draft or pending verification incoming funds can be confirmed.'))
            previous = incoming.state
            incoming._create_movement(
                purpose='confirm',
                movement_type='incoming_confirm',
                bucket='account_unassigned',
                direction='in',
                amount=incoming.amount,
                fund_account=incoming.fund_account_id,
                description=incoming.transaction_reference,
            )
            incoming.write({'state': 'confirmed'})
            incoming._history('approve', previous, 'confirmed', amount=incoming.amount, fund_account=incoming.fund_account_id)
            incoming.message_post(body=_('Incoming fund confirmed.'))

    def action_cancel(self):
        for incoming in self:
            if incoming.state == 'confirmed' and not incoming._is_finance():
                raise AccessError(_('Only finance users can cancel confirmed incoming funds.'))
            if incoming.state == 'cancelled':
                continue
            previous = incoming.state
            if incoming.state == 'confirmed':
                incoming._create_movement(
                    purpose='cancel',
                    movement_type='incoming_cancel',
                    bucket='account_unassigned',
                    direction='out',
                    amount=incoming.amount,
                    fund_account=incoming.fund_account_id,
                    description=incoming.transaction_reference,
                )
            incoming.write({'state': 'cancelled'})
            incoming._history('cancel', previous, 'cancelled', amount=incoming.amount, fund_account=incoming.fund_account_id)

    def unlink(self):
        for incoming in self:
            if incoming.state == 'confirmed':
                raise UserError(_('Confirmed incoming funds cannot be deleted. Cancel or reverse records instead.'))
        return super().unlink()


class FundAllocation(models.Model):
    _name = 'fund.allocation'
    _description = 'Fund Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fund.request.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'), tracking=True)
    fund_account_id = fields.Many2one('fund.account', required=True, tracking=True, check_company=True)
    project_id = fields.Many2one('project.project', check_company=True)
    expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    amount = fields.Monetary(required=True, currency_field='currency_id', tracking=True)
    purpose = fields.Text(required=True)
    request_date = fields.Date(default=fields.Date.context_today, required=True)
    requested_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('gm_approved', 'GM Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)
    approval_step_ids = fields.One2many('fund.approval.step', 'allocation_id', string='Approval Steps')
    approval_history_ids = fields.One2many('fund.approval.history', 'allocation_id', string='Approval History')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('fund.allocation') or _('New')
        return super().create(vals_list)

    @api.constrains('project_id', 'expense_head_id')
    def _check_single_target(self):
        for allocation in self:
            if bool(allocation.project_id) == bool(allocation.expense_head_id):
                raise ValidationError(_('Choose either a project or an expense head.'))

    def action_submit(self):
        self._check_group('nn_fund_management.group_fund_user', _('Only fund users can submit allocations.'))
        for allocation in self:
            allocation._check_positive_amount()
            if allocation.state != 'draft':
                raise UserError(_('Only draft allocations can be submitted.'))
            allocation.fund_account_id._lock_company_scope()
            rules = allocation._matching_approval_rules('allocation')
            if allocation.amount > allocation.fund_account_id.available_unassigned_balance:
                raise ValidationError(_('Allocation amount cannot exceed available unassigned balance.'))
            allocation._create_movement('submit_unassigned', 'allocation_submit', 'account_unassigned', 'out', allocation.amount, fund_account=allocation.fund_account_id)
            allocation._create_movement('submit_hold', 'allocation_submit', 'account_allocation_hold', 'in', allocation.amount, fund_account=allocation.fund_account_id)
            previous = allocation.state
            allocation.write({'state': 'submitted'})
            allocation._create_approval_steps('allocation', rules=rules)
            allocation._history('submit', previous, 'submitted', amount=allocation.amount, fund_account=allocation.fund_account_id)
            allocation.message_post(body=_('Allocation submitted.'))

    def action_approve(self, comment=None):
        for allocation in self:
            if allocation.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only submitted allocations can be approved.'))
            previous = allocation.state
            allocation._approve_step(comment=comment)
            if allocation._pending_step():
                allocation.write({'state': 'gm_approved'})
                allocation._schedule_current_approver_activity()
            else:
                allocation._create_movement('approve_hold', 'allocation_approve', 'account_allocation_hold', 'out', allocation.amount, fund_account=allocation.fund_account_id)
                allocation._create_target_movement('approve_target', 'allocation_approve', 'available', 'in', allocation.amount, description=allocation.purpose)
                allocation.write({'state': 'approved'})
                allocation._history('approve', previous, 'approved', amount=allocation.amount, fund_account=allocation.fund_account_id)
                allocation.message_post(body=_('Allocation approved and assigned.'))

    def action_reject(self, comment=None):
        for allocation in self:
            if allocation.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only pending allocations can be rejected.'))
            allocation._reject_step(comment=comment)
            allocation._release_hold('rejected')

    def action_cancel(self):
        for allocation in self:
            if allocation.state == 'approved' and not allocation._is_finance():
                raise AccessError(_('Only finance users can cancel approved allocations.'))
            if allocation.state in ('rejected', 'cancelled'):
                continue
            previous = allocation.state
            if allocation.state in ('submitted', 'gm_approved'):
                allocation._release_hold('cancelled')
            elif allocation.state == 'approved':
                project, expense = allocation._target_values()
                if allocation.amount > allocation._target_balance('available', project=project, expense=expense):
                    raise ValidationError(_('This approved allocation cannot be cancelled because the target balance has already been used.'))
                allocation._create_target_movement('cancel_target', 'allocation_release', 'available', 'out', allocation.amount, project=project, expense=expense)
                allocation._create_movement('cancel_unassigned', 'allocation_release', 'account_unassigned', 'in', allocation.amount, fund_account=allocation.fund_account_id)
                allocation.write({'state': 'cancelled'})
            else:
                allocation.write({'state': 'cancelled'})
            allocation._history('cancel', previous, 'cancelled', amount=allocation.amount, fund_account=allocation.fund_account_id)

    def _release_hold(self, final_state):
        self.ensure_one()
        self._create_movement(final_state + '_hold', 'allocation_release', 'account_allocation_hold', 'out', self.amount, fund_account=self.fund_account_id)
        self._create_movement(final_state + '_unassigned', 'allocation_release', 'account_unassigned', 'in', self.amount, fund_account=self.fund_account_id)
        previous = self.state
        self.write({'state': final_state})
        self._history('cancel' if final_state == 'cancelled' else 'reject', previous, final_state, amount=self.amount, fund_account=self.fund_account_id)

    def unlink(self):
        for allocation in self:
            if allocation.state not in ('draft', 'cancelled'):
                raise UserError(_('Submitted financial requests cannot be deleted. Cancel or reject them instead.'))
        return super().unlink()


class FundRequisition(models.Model):
    _name = 'fund.requisition'
    _description = 'Fund Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fund.request.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'), tracking=True)
    project_id = fields.Many2one('project.project', check_company=True)
    expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    amount = fields.Monetary(required=True, currency_field='currency_id', tracking=True)
    purpose = fields.Text(required=True)
    request_date = fields.Date(default=fields.Date.context_today, required=True)
    required_date = fields.Date()
    requested_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Attachments')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('gm_approved', 'GM Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True)
    bill_ids = fields.One2many('fund.bill', 'requisition_id')
    billed_amount = fields.Monetary(compute='_compute_bill_amounts', currency_field='currency_id')
    remaining_billable_amount = fields.Monetary(compute='_compute_bill_amounts', currency_field='currency_id')
    released_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    approval_step_ids = fields.One2many('fund.approval.step', 'requisition_id', string='Approval Steps')
    approval_history_ids = fields.One2many('fund.approval.history', 'requisition_id', string='Approval History')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('fund.requisition') or _('New')
        return super().create(vals_list)

    @api.constrains('project_id', 'expense_head_id')
    def _check_single_target(self):
        for requisition in self:
            if bool(requisition.project_id) == bool(requisition.expense_head_id):
                raise ValidationError(_('Choose either a project or an expense head.'))

    @api.depends('bill_ids.state', 'bill_ids.amount', 'released_amount', 'amount')
    def _compute_bill_amounts(self):
        for requisition in self:
            requisition.billed_amount = sum(requisition.bill_ids.filtered(lambda bill: bill.state == 'posted').mapped('amount'))
            requisition.remaining_billable_amount = max(requisition.amount - requisition.billed_amount - requisition.released_amount, 0.0)

    def action_submit(self):
        self._check_group('nn_fund_management.group_fund_user', _('Only fund users can submit requisitions.'))
        for requisition in self:
            requisition._check_positive_amount()
            if requisition.state != 'draft':
                raise UserError(_('Only draft requisitions can be submitted.'))
            project, expense = requisition._target_values()
            requisition._lock_target_scope(project=project, expense=expense)
            rules = requisition._matching_approval_rules('requisition')
            if requisition.amount > requisition._target_balance('available', project=project, expense=expense):
                raise ValidationError(_('Requisition amount cannot exceed available target balance.'))
            requisition._create_target_movement('submit_available', 'requisition_submit', 'available', 'out', requisition.amount, project=project, expense=expense)
            requisition._create_target_movement('submit_hold', 'requisition_submit', 'requisition_hold', 'in', requisition.amount, project=project, expense=expense)
            previous = requisition.state
            requisition.write({'state': 'submitted'})
            requisition._create_approval_steps('requisition', rules=rules)
            requisition._history('submit', previous, 'submitted', amount=requisition.amount, project=project, expense_head=expense)
            requisition.message_post(body=_('Requisition submitted.'))

    def action_approve(self, comment=None):
        for requisition in self:
            if requisition.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only submitted requisitions can be approved.'))
            previous = requisition.state
            requisition._approve_step(comment=comment)
            if requisition._pending_step():
                requisition.write({'state': 'gm_approved'})
                requisition._schedule_current_approver_activity()
            else:
                project, expense = requisition._target_values()
                requisition._create_target_movement('approve_hold', 'requisition_approve', 'requisition_hold', 'out', requisition.amount, project=project, expense=expense)
                requisition._create_target_movement('approve_reserved', 'requisition_approve', 'reserved', 'in', requisition.amount, project=project, expense=expense)
                requisition.write({'state': 'approved'})
                requisition._history('approve', previous, 'approved', amount=requisition.amount, project=project, expense_head=expense)
                requisition.message_post(body=_('Requisition approved.'))

    def action_reject(self, comment=None):
        for requisition in self:
            if requisition.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only pending requisitions can be rejected.'))
            requisition._reject_step(comment=comment)
            requisition._release_hold('rejected')

    def action_cancel(self):
        for requisition in self:
            if requisition.state == 'approved' and not requisition._is_finance():
                raise AccessError(_('Only finance users can cancel approved requisitions.'))
            if requisition.state in ('rejected', 'cancelled', 'closed'):
                continue
            previous = requisition.state
            if requisition.state in ('submitted', 'gm_approved'):
                requisition._release_hold('cancelled')
            elif requisition.state == 'approved':
                requisition._release_unused('cancelled')
            else:
                requisition.write({'state': 'cancelled'})
            requisition._history('cancel', previous, 'cancelled')

    def action_close(self):
        for requisition in self:
            if requisition.state != 'approved':
                raise UserError(_('Only approved requisitions can be closed.'))
            previous = requisition.state
            if requisition.remaining_billable_amount:
                requisition._release_unused('closed')
            else:
                requisition.write({'state': 'closed'})
            requisition._history('close', previous, 'closed')

    def _release_hold(self, final_state):
        self.ensure_one()
        project, expense = self._target_values()
        self._create_target_movement(final_state + '_hold', 'requisition_release', 'requisition_hold', 'out', self.amount, project=project, expense=expense)
        self._create_target_movement(final_state + '_available', 'requisition_release', 'available', 'in', self.amount, project=project, expense=expense)
        previous = self.state
        self.write({'state': final_state})
        self._history('cancel' if final_state == 'cancelled' else 'reject', previous, final_state, project=project, expense_head=expense)

    def _release_unused(self, final_state):
        self.ensure_one()
        project, expense = self._target_values()
        amount = self.remaining_billable_amount
        if amount:
            self._create_target_movement(final_state + '_reserved', 'requisition_release', 'reserved', 'out', amount, project=project, expense=expense)
            self._create_target_movement(final_state + '_available', 'requisition_release', 'available', 'in', amount, project=project, expense=expense)
            self.released_amount += amount
        self.write({'state': final_state})

    def unlink(self):
        for requisition in self:
            if requisition.state not in ('draft', 'cancelled'):
                raise UserError(_('Submitted financial requests cannot be deleted. Cancel or reject them instead.'))
        return super().unlink()


class FundBill(models.Model):
    _name = 'fund.bill'
    _description = 'Fund Bill'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fund.request.mixin']
    _order = 'bill_date desc, id desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'), tracking=True)
    requisition_id = fields.Many2one('fund.requisition', required=True, check_company=True, ondelete='restrict')
    project_id = fields.Many2one('project.project', check_company=True)
    expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    bill_date = fields.Date(default=fields.Date.context_today, required=True)
    amount = fields.Monetary(required=True, currency_field='currency_id', tracking=True)
    vendor = fields.Char()
    description = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('reversed', 'Reversed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        records = super().create(vals_list)
        for record in records:
            if record.name == _('New'):
                record.name = seq.next_by_code('fund.bill') or _('New')
            if not record.project_id and not record.expense_head_id and record.requisition_id:
                record.project_id = record.requisition_id.project_id
                record.expense_head_id = record.requisition_id.expense_head_id
        return records

    @api.constrains('project_id', 'expense_head_id', 'requisition_id')
    def _check_requisition_target(self):
        for bill in self:
            if bool(bill.project_id) == bool(bill.expense_head_id):
                raise ValidationError(_('Choose either a project or an expense head.'))
            if bill.requisition_id:
                if bill.project_id != bill.requisition_id.project_id or bill.expense_head_id != bill.requisition_id.expense_head_id:
                    raise ValidationError(_('A bill must use the same project or expense head as its requisition.'))

    def action_post(self):
        self._check_group('nn_fund_management.group_finance_user', _('Only finance users can post bills.'))
        for bill in self:
            bill._check_positive_amount()
            if bill.state != 'draft':
                raise UserError(_('Only draft bills can be posted.'))
            if bill.requisition_id.state != 'approved':
                raise ValidationError(_('Only approved requisitions can be used for bills.'))
            if bill.amount > bill.requisition_id.remaining_billable_amount:
                raise ValidationError(_('A bill cannot exceed the requisition remaining billable amount.'))
            project, expense = bill.requisition_id._target_values()
            bill._create_target_movement('post_reserved', 'bill_post', 'reserved', 'out', bill.amount, project=project, expense=expense)
            bill._create_target_movement('post_spent', 'bill_post', 'spent', 'in', bill.amount, project=project, expense=expense)
            previous = bill.state
            bill.write({'state': 'posted'})
            bill._history('post', previous, 'posted', project=project, expense_head=expense)
            if bill.requisition_id.remaining_billable_amount <= bill.requisition_id.amount * 0.1:
                bill.requisition_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=bill.requisition_id.requested_by_id.id,
                    summary=_('Requisition almost fully used'),
                    note=_('%s has %s remaining.') % (bill.requisition_id.display_name, bill.requisition_id.remaining_billable_amount),
                )

    def action_reverse(self):
        self._check_group('nn_fund_management.group_finance_user', _('Only finance users can reverse bills.'))
        for bill in self:
            if bill.state != 'posted':
                raise UserError(_('Only posted bills can be reversed.'))
            if bill.requisition_id.state == 'closed':
                raise ValidationError(_('Bills cannot be reversed after the requisition is closed.'))
            project, expense = bill.requisition_id._target_values()
            bill._create_target_movement('reverse_spent', 'bill_reverse', 'spent', 'out', bill.amount, project=project, expense=expense)
            bill._create_target_movement('reverse_reserved', 'bill_reverse', 'reserved', 'in', bill.amount, project=project, expense=expense)
            previous = bill.state
            bill.write({'state': 'reversed'})
            bill._history('reverse', previous, 'reversed', project=project, expense_head=expense)

    def action_cancel(self):
        for bill in self:
            if bill.state == 'posted':
                raise UserError(_('Posted bills must be reversed, not cancelled.'))
            previous = bill.state
            bill.write({'state': 'cancelled'})
            bill._history('cancel', previous, 'cancelled')

    def unlink(self):
        for bill in self:
            if bill.state in ('posted', 'reversed'):
                raise UserError(_('Posted or reversed bills cannot be deleted.'))
        return super().unlink()


class FundTransfer(models.Model):
    _name = 'fund.transfer'
    _description = 'Fund Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fund.request.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'), tracking=True)
    source_project_id = fields.Many2one('project.project', check_company=True)
    source_expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    destination_project_id = fields.Many2one('project.project', check_company=True)
    destination_expense_head_id = fields.Many2one('fund.expense.head', check_company=True)
    amount = fields.Monetary(required=True, currency_field='currency_id', tracking=True)
    reason = fields.Text(required=True)
    request_date = fields.Date(default=fields.Date.context_today, required=True)
    requested_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('gm_approved', 'GM Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)
    approval_step_ids = fields.One2many('fund.approval.step', 'transfer_id', string='Approval Steps')
    approval_history_ids = fields.One2many('fund.approval.history', 'transfer_id', string='Approval History')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('fund.transfer') or _('New')
        return super().create(vals_list)

    @api.constrains('source_project_id', 'source_expense_head_id', 'destination_project_id', 'destination_expense_head_id')
    def _check_targets(self):
        for transfer in self:
            if bool(transfer.source_project_id) == bool(transfer.source_expense_head_id):
                raise ValidationError(_('Choose either a source project or source expense head.'))
            if bool(transfer.destination_project_id) == bool(transfer.destination_expense_head_id):
                raise ValidationError(_('Choose either a destination project or destination expense head.'))
            if transfer.source_project_id and transfer.source_project_id == transfer.destination_project_id:
                raise ValidationError(_('Source and destination cannot be the same.'))
            if transfer.source_expense_head_id and transfer.source_expense_head_id == transfer.destination_expense_head_id:
                raise ValidationError(_('Source and destination cannot be the same.'))

    def _source(self):
        self.ensure_one()
        return self.source_project_id, self.source_expense_head_id

    def _destination(self):
        self.ensure_one()
        return self.destination_project_id, self.destination_expense_head_id

    def action_submit(self):
        self._check_group('nn_fund_management.group_fund_user', _('Only fund users can submit transfers.'))
        for transfer in self:
            transfer._check_positive_amount()
            if transfer.state != 'draft':
                raise UserError(_('Only draft transfers can be submitted.'))
            source_project, source_expense = transfer._source()
            transfer._lock_target_scope(project=source_project, expense=source_expense)
            rules = transfer._matching_approval_rules('transfer')
            if transfer.amount > transfer._target_balance('available', project=source_project, expense=source_expense):
                raise ValidationError(_('Transfer amount cannot exceed source available balance.'))
            transfer._create_target_movement('submit_available', 'transfer_submit', 'available', 'out', transfer.amount, project=source_project, expense=source_expense)
            transfer._create_target_movement('submit_hold', 'transfer_submit', 'transfer_hold', 'in', transfer.amount, project=source_project, expense=source_expense)
            previous = transfer.state
            transfer.write({'state': 'submitted'})
            transfer._create_approval_steps('transfer', rules=rules)
            transfer._history('submit', previous, 'submitted', amount=transfer.amount, project=source_project, expense_head=source_expense)
            transfer.message_post(body=_('Transfer submitted.'))

    def action_approve(self, comment=None):
        for transfer in self:
            if transfer.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only submitted transfers can be approved.'))
            previous = transfer.state
            transfer._approve_step(comment=comment)
            if transfer._pending_step():
                transfer.write({'state': 'gm_approved'})
                transfer._schedule_current_approver_activity()
            else:
                source_project, source_expense = transfer._source()
                dest_project, dest_expense = transfer._destination()
                transfer._create_target_movement('approve_hold', 'transfer_approve', 'transfer_hold', 'out', transfer.amount, project=source_project, expense=source_expense)
                transfer._create_target_movement('approve_destination', 'transfer_approve', 'available', 'in', transfer.amount, project=dest_project, expense=dest_expense)
                transfer.write({'state': 'approved'})
                transfer._history('approve', previous, 'approved', amount=transfer.amount, project=source_project, expense_head=source_expense)
                transfer.message_post(body=_('Transfer approved.'))

    def action_reject(self, comment=None):
        for transfer in self:
            if transfer.state not in ('submitted', 'gm_approved'):
                raise UserError(_('Only pending transfers can be rejected.'))
            transfer._reject_step(comment=comment)
            transfer._release_hold('rejected')

    def action_cancel(self):
        for transfer in self:
            if transfer.state == 'approved':
                raise UserError(_('Approved transfers cannot be cancelled after destination funding is created.'))
            if transfer.state in ('rejected', 'cancelled'):
                continue
            if transfer.state in ('submitted', 'gm_approved'):
                transfer._release_hold('cancelled')
            else:
                previous = transfer.state
                transfer.write({'state': 'cancelled'})
                transfer._history('cancel', previous, 'cancelled')

    def _release_hold(self, final_state):
        self.ensure_one()
        source_project, source_expense = self._source()
        self._create_target_movement(final_state + '_hold', 'transfer_release', 'transfer_hold', 'out', self.amount, project=source_project, expense=source_expense)
        self._create_target_movement(final_state + '_available', 'transfer_release', 'available', 'in', self.amount, project=source_project, expense=source_expense)
        previous = self.state
        self.write({'state': final_state})
        self._history('cancel' if final_state == 'cancelled' else 'reject', previous, final_state, project=source_project, expense_head=source_expense)

    def unlink(self):
        for transfer in self:
            if transfer.state not in ('draft', 'cancelled'):
                raise UserError(_('Submitted financial requests cannot be deleted. Cancel or reject them instead.'))
        return super().unlink()


class FundBankEmail(models.Model):
    _name = 'fund.bank.email'
    _description = 'Bank Email Import'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'email_date desc, id desc'

    name = fields.Char(required=True, default=lambda self: _('Bank Email'))
    fund_account_id = fields.Many2one('fund.account', required=True, check_company=True)
    email_message_id = fields.Char(required=True, index=True)
    email_date = fields.Datetime(default=fields.Datetime.now)
    raw_body = fields.Text(required=True)
    bank_name = fields.Char()
    masked_account_number = fields.Char()
    transaction_reference = fields.Char()
    transaction_date = fields.Date()
    received_amount = fields.Monetary(currency_field='currency_id')
    sender_info = fields.Char()
    incoming_id = fields.Many2one('fund.incoming', readonly=True)
    parse_error = fields.Text(readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('parsed', 'Parsed'),
        ('failed', 'Failed'),
        ('created', 'Incoming Created'),
    ], default='draft', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    _email_message_unique = models.Constraint(
        'unique(email_message_id)',
        'The same bank email cannot be processed twice.',
    )

    def action_parse(self):
        amount_pattern = re.compile(r'(?:BDT|Tk\.?|Amount)\s*[:\-]?\s*([0-9,]+(?:\.[0-9]+)?)', re.IGNORECASE)
        ref_pattern = re.compile(r'(?:Ref|Reference|Txn|Transaction)\s*[:#\-]?\s*([A-Za-z0-9\-_/]+)', re.IGNORECASE)
        account_pattern = re.compile(r'(?:Account|A/C)\s*[:#\-]?\s*([Xx*\d\-]{4,})', re.IGNORECASE)
        date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        for email in self:
            amount = amount_pattern.search(email.raw_body or '')
            ref = ref_pattern.search(email.raw_body or '')
            account = account_pattern.search(email.raw_body or '')
            tx_date = date_pattern.search(email.raw_body or '')
            if not amount or not ref:
                email.write({
                    'state': 'failed',
                    'parse_error': _('Could not find both amount and transaction reference.'),
                })
                email.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=self.env.user.id,
                    summary=_('Bank email parsing failed'),
                    note=email.parse_error,
                )
                continue
            email.write({
                'received_amount': float(amount.group(1).replace(',', '')),
                'transaction_reference': ref.group(1),
                'masked_account_number': account.group(1) if account else False,
                'transaction_date': tx_date.group(1) if tx_date else fields.Date.context_today(email),
                'sender_info': email.sender_info or email.bank_name,
                'state': 'parsed',
                'parse_error': False,
            })

    def action_create_incoming(self):
        for email in self:
            if email.state != 'parsed':
                raise UserError(_('Only parsed bank emails can create incoming funds.'))
            duplicate = self.env['fund.incoming'].search([
                ('fund_account_id', '=', email.fund_account_id.id),
                ('transaction_reference', '=', email.transaction_reference),
            ], limit=1)
            if duplicate:
                raise ValidationError(_('Duplicate transaction reference detected.'))
            incoming = self.env['fund.incoming'].create({
                'fund_account_id': email.fund_account_id.id,
                'date': email.transaction_date or fields.Date.context_today(email),
                'amount': email.received_amount,
                'transaction_reference': email.transaction_reference,
                'sender': email.sender_info or email.bank_name,
                'description': _('Created from bank email %s') % email.email_message_id,
                'company_id': email.company_id.id,
                'state': 'pending_verification',
            })
            email.write({'incoming_id': incoming.id, 'state': 'created'})


class FundDashboard(models.Model):
    _name = 'fund.dashboard'
    _description = 'Fund Dashboard'

    name = fields.Char(default='Fund Dashboard')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    total_received = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    unassigned_balance = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    held_amount = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    assigned_amount = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    spent_amount = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    pending_approval_count = fields.Integer(compute='_compute_totals')
    recent_movement_ids = fields.Many2many('fund.movement', compute='_compute_recent_movements')

    def _compute_totals(self):
        for dashboard in self:
            company = dashboard.company_id or self.env.company
            accounts = self.env['fund.account'].search([('company_id', '=', company.id)])
            dashboard.total_received = sum(accounts.mapped('total_received'))
            dashboard.unassigned_balance = sum(accounts.mapped('available_unassigned_balance'))
            dashboard.held_amount = sum(accounts.mapped('allocation_hold_amount'))
            project_movements = self.env['fund.movement'].search([('company_id', '=', company.id), ('project_id', '!=', False)])
            expense_movements = self.env['fund.movement'].search([('company_id', '=', company.id), ('expense_head_id', '!=', False)])
            target_movements = project_movements + expense_movements
            dashboard.assigned_amount = sum(target_movements.filtered(lambda move: move.bucket in ('target_available', 'target_requisition_hold', 'target_transfer_hold', 'target_reserved', 'target_spent')).mapped('signed_amount'))
            dashboard.spent_amount = sum(target_movements.filtered(lambda move: move.bucket == 'target_spent').mapped('signed_amount'))
            dashboard.pending_approval_count = self.env['fund.approval.step'].search_count([('company_id', '=', company.id), ('state', '=', 'pending')])

    def _compute_recent_movements(self):
        for dashboard in self:
            dashboard.recent_movement_ids = self.env['fund.movement'].search([('company_id', '=', (dashboard.company_id or self.env.company).id)], limit=10)
