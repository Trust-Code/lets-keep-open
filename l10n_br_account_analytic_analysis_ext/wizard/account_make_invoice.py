# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_make_invoice(osv.osv_memory):
    _name = 'account.make.invoice'
    _description = 'Account Make Invoice'
    _columns = {'limit_date': fields.date('Limit for Invoice Create')}
    _defaults = {'limit_date': fields.date.context_today}

    def make_invoices(self, cr, uid, ids, context=None):
        obj_account_analytic_analysis = self.pool.get('account.analytic.account')
        if context is None:
            context = {}
        w_form_data = self.read(cr, uid, ids)[0]
        obj_account_analytic_analysis.action_create_invoice(
            cr, uid, context.get('active_ids'),
            limit_date=w_form_data['limit_date'], context=None)
        return


account_make_invoice()
