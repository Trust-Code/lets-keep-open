# Embedded file name: /opt/openerp/producao/addons-extension/l10n_br_account_ext/account.py
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp

class account_tax_code(osv.osv):
    _name = 'account.tax.code'
    _inherit = 'account.tax.code'
    _columns = {'tax_retain_amount': fields.float('Tax Retain Amount', digits_compute=dp.get_precision('Account')),
     'tax_retain_type': fields.selection([('no_retain', 'No Retain'), ('by_invoice', 'By Invoice'), ('inv_amount_monthly', 'Invoice Amount Monthly')], 'Tax Retain Type'),
     'invoice_tax_retain_account': fields.many2one('account.account', 'Invoice Tax Retain Account'),
     'refund_tax_retain_account': fields.many2one('account.account', 'Refund Tax Retain Account'),
     'account_collected_deduct_id': fields.many2one('account.account', 'Invoice Deduct Tax Account', help='Set the account that will be set by deduct on invoice tax lines for invoices. Leave empty to not use deduction account tax.')}
    _defaults = {'tax_retain_type': 'no_retain'}


class account_move(osv.osv):
    _inherit = 'account.move'

    def onchange_journal_id(self, cr, uid, ids, journal_id, context = None):
        if context is None:
            context = {}
        company_id = False
        period_obj = self.pool.get('account.period')
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            if journal.company_id.id:
                company_id = journal.company_id.id
        ctx = context.copy()
        ctx.update({'company_id': company_id,
         'account_period_prefer_normal': True})
        return {'value': {'company_id': company_id,
                   'period_id': period_obj.find(cr, uid, fields.date.today(), context=ctx)[0]}}

    def create(self, cr, uid, vals, context = None):
        if context is None:
            context = {}
        journal_id = vals['journal_id']
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            if journal.company_id.id:
                vals['company_id'] = journal.company_id.id
        return super(account_move, self).create(cr, uid, vals, context)


class account_bank_statement(osv.osv):
    _name = 'account.bank.statement'
    _inherit = 'account.bank.statement'

    def create(self, cr, uid, vals, context = None):
        if context is None:
            context = {}
        journal_id = vals['journal_id']
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            if journal.company_id.id:
                vals['company_id'] = journal.company_id.id
        return super(account_bank_statement, self).create(cr, uid, vals, context=context)


account_bank_statement()