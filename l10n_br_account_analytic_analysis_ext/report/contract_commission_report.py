# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_account_analytic_analysis_ext/report/contract_commission_report.py
from openerp import tools
from openerp.osv import fields, osv

class contract_partner_commission_report(osv.osv):
    _name = 'contract.partner.commission.report'
    _description = 'Contract Partner Commission Report'
    _auto = False
    _columns = {'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
     'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
     'period_id': fields.many2one('account.period', 'Period', readonly=True),
     'internal_number': fields.char('Invoice Number', size=32, readonly=True),
     'received': fields.float('Payment Value', digits=(16, 2), readonly=True),
     'date': fields.date('Payment Date', readonly=True),
     'perc_commission': fields.float('Perc. Commission %', digits=(16, 2), readonly=True),
     'value_commission': fields.float('Commission Value', digits=(16, 2), readonly=True),
     'state': fields.char('Status', readonly=True),
     'move_line_id': fields.many2one('account.move.line', 'Payment', readonly=True),
     'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
     'customer_id': fields.many2one('res.partner', 'Customer', readonly=True)}
    _order = 'period_id, partner_id'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'contract_partner_commission_report')
        cr.execute('\n            create or replace view contract_partner_commission_report as (\n                SELECT\n                    row_number() OVER() AS id,\n                    aapc.partner_id AS partner_id,\n                    ail.account_analytic_id AS analytic_account_id,\n                    aml.period_id AS period_id,\n                    ai.internal_number AS internal_number,\n                    aml.id AS move_line_id,\n                    min(ai.state) AS state,\n                    sum(aml.credit) AS received,\n                    min(aml.date) AS date,\n                    min(aapc.partner_commission) AS perc_commission,\n                    sum(aml.credit * aapc.partner_commission / 100) AS value_commission,\n                    min(ai.id) AS invoice_id,\n                    min(ai.partner_id) AS customer_id\n                FROM\n                    account_move_reconcile AS amr\n                    INNER JOIN account_move_line AS aml ON ((aml.reconcile_id=amr.id OR aml.reconcile_partial_id=amr.id) AND aml.credit>0)\n                    INNER JOIN account_move_line AS amlv ON ((amlv.reconcile_id=amr.id OR amlv.reconcile_partial_id=amr.id) AND amlv.debit>0)\n                    INNER JOIN account_invoice AS ai ON (amlv.move_id=ai.move_id)\n                    INNER JOIN account_invoice_line AS ail ON (ail.invoice_id=ai.id)\n                    INNER JOIN account_analytic_partner_commission AS aapc ON (ail.account_analytic_id=aapc.analytic_account_id)\n                GROUP BY\n                    aapc.partner_id,\n                    ail.account_analytic_id,\n                    ai.period_id,\n                    ai.internal_number,\n                    aml.id\n                )\n            ')


contract_partner_commission_report()

class contract_salesperson_commission_report(osv.osv):
    _name = 'contract.salesperson.commission.report'
    _description = 'Contract Salesperson Commission Report'
    _auto = False
    _columns = {'salesperson_id': fields.many2one('res.users', 'Salesperson', readonly=True),
     'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
     'period_id': fields.many2one('account.period', 'Period', readonly=True),
     'internal_number': fields.char('Invoice Number', size=32, readonly=True),
     'received': fields.float('Payment Value', digits=(16, 2), readonly=True),
     'perc_commission': fields.float('Perc. Commission %', digits=(16, 2), readonly=True),
     'value_commission': fields.float('Commission Value', digits=(16, 2), readonly=True),
     'state': fields.char('Status', readonly=True),
     'move_line_id': fields.many2one('account.move.line', 'Payment', readonly=True),
     'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
     'customer_id': fields.many2one('res.partner', 'Customer', readonly=True)}
    _order = 'period_id, salesperson_id'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'contract_salesperson_commission_report')
        cr.execute('\n            create or replace view contract_salesperson_commission_report as (\n                SELECT\n                    row_number() OVER() AS id,\n                    aaa.salesperson_id AS salesperson_id,\n                    ail.account_analytic_id AS analytic_account_id,\n                    aml.period_id AS period_id,\n                    ai.internal_number AS internal_number,\n                    aml.id AS move_line_id,\n                    min(ai.state) AS state,\n                    sum(aml.credit) AS received,\n                    min(aml.date) AS date,\n                    min(aapc.partner_commission) AS perc_commission,\n                    sum(aml.credit * aapc.partner_commission / 100) AS value_commission,\n                    min(ai.id) AS invoice_id,\n                    min(ai.partner_id) AS customer_id\n                FROM\n                    account_move_reconcile AS amr\n                    INNER JOIN account_move_line AS aml ON ((aml.reconcile_id=amr.id OR aml.reconcile_partial_id=amr.id) AND aml.credit>0)\n                    INNER JOIN account_move_line AS amlv ON ((amlv.reconcile_id=amr.id OR amlv.reconcile_partial_id=amr.id) AND amlv.debit>0)\n                    INNER JOIN account_invoice AS ai ON (amlv.move_id=ai.move_id)\n                    INNER JOIN account_invoice_line AS ail ON (ail.invoice_id=ai.id)\n                    INNER JOIN account_analytic_partner_commission AS aapc ON (ail.account_analytic_id=aapc.analytic_account_id)\n                    INNER JOIN account_analytic_account AS aaa ON (ail.account_analytic_id=aaa.id)\n                WHERE\n                    aaa.salesperson_id is not null\n                GROUP BY\n                    aaa.salesperson_id,\n                    ail.account_analytic_id,\n                    ai.period_id,\n                    ai.internal_number,\n                    aml.id\n                )\n        ')


contract_partner_commission_report()