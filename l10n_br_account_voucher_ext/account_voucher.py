# Embedded file name: /opt/openerp/producao/addons-extension/l10n_br_account_voucher_ext/account_voucher.py
from openerp.osv import fields, osv

class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    def onchange_company_id(self, cr, uid, ids, company_id, context = None):
        if context is None:
            context = {}
        context.update({'company_id': company_id})
        w_period_ids = self.pool.get('account.period').find(cr, uid, context=context)
        return {'value': {'period_id': w_period_ids and w_period_ids[0] or False}}


account_voucher()