from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    fund_movement_ids = fields.One2many('fund.movement', 'project_id')
    fund_total_allocated = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_available = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_requisition_hold = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_transfer_hold = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_approved_unspent = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_total_spent = fields.Monetary(compute='_compute_fund_balances', currency_field='currency_id')
    fund_incoming_transfers = fields.Monetary(compute='_compute_fund_transfer_totals', currency_field='currency_id')
    fund_outgoing_transfers = fields.Monetary(compute='_compute_fund_transfer_totals', currency_field='currency_id')

    @api.depends('fund_movement_ids.signed_amount', 'fund_movement_ids.bucket')
    def _compute_fund_balances(self):
        grouped = self.env['fund.movement']._read_group(
            [('project_id', 'in', self.ids)],
            ['project_id', 'bucket'],
            ['signed_amount:sum'],
        )
        totals = {}
        for project, bucket, signed_amount_sum in grouped:
            totals.setdefault(project.id, {})[bucket] = signed_amount_sum
        for project in self:
            values = totals.get(project.id, {})
            project.fund_available = values.get('target_available', 0.0)
            project.fund_requisition_hold = values.get('target_requisition_hold', 0.0)
            project.fund_transfer_hold = values.get('target_transfer_hold', 0.0)
            project.fund_approved_unspent = values.get('target_reserved', 0.0)
            project.fund_total_spent = values.get('target_spent', 0.0)
            project.fund_total_allocated = (
                project.fund_available
                + project.fund_requisition_hold
                + project.fund_transfer_hold
                + project.fund_approved_unspent
                + project.fund_total_spent
            )

    def _compute_fund_transfer_totals(self):
        for project in self:
            incoming = self.env['fund.movement']._read_group([
                ('project_id', '=', project.id),
                ('movement_type', '=', 'transfer_approve'),
                ('bucket', '=', 'target_available'),
                ('direction', '=', 'in'),
            ], [], ['amount:sum'])
            outgoing = self.env['fund.movement']._read_group([
                ('project_id', '=', project.id),
                ('movement_type', '=', 'transfer_submit'),
                ('bucket', '=', 'target_transfer_hold'),
                ('direction', '=', 'in'),
            ], [], ['amount:sum'])
            project.fund_incoming_transfers = incoming[0][0] if incoming else 0.0
            project.fund_outgoing_transfers = outgoing[0][0] if outgoing else 0.0
