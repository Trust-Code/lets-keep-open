# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_base_ext/res_company.py
from openerp.osv import orm, fields

class res_company(orm.Model):
    _inherit = 'res.company'
    _columns = {'partner_default_account_payable_id': fields.many2one('account.account', 'Account Payable', domain="[('type', '=', 'payable')]"),
     'partner_default_account_receivable_id': fields.many2one('account.account', 'Account Receivable', domain="[('type', '=', 'receivable')]"),
     'partner_default_fiscal_type_id': fields.many2one('l10n_br_account.partner.fiscal.type', 'Fiscal Type')}

    def _company_default_get(self, cr, uid, object = False, field = False, context = None):
        if not context:
            context = {}
        company_id = super(res_company, self)._company_default_get(cr, uid, object=object, field=field, context=context)
        journal_id = context.get('default_journal_id') or False
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            if journal.company_id.id:
                company_id = journal.company_id.id
        return company_id


res_company()