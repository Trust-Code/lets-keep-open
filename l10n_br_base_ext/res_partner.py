# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'parent_id': fields.many2one('res.partner', 'Related Company')
    }

    def _get_account_payable(self, cr, uid, ids, context=None):
        w_res_company_id = self.pool.get('res.company')._company_default_get(cr, uid, object='res.company', field='property_account_payable', context=context)
        br_res_company = self.pool.get('res.company').browse(cr, uid, w_res_company_id, context=context)
        return br_res_company.partner_default_account_payable_id.id

    def _get_account_receivable(self, cr, uid, ids, context=None):
        w_res_company_id = self.pool.get('res.company')._company_default_get(cr, uid, object='res.company', field='property_account_payable', context=context)
        br_res_company = self.pool.get('res.company').browse(cr, uid, w_res_company_id, context=context)
        return br_res_company.partner_default_account_receivable_id.id

    def _get_fiscal_type(self, cr, uid, ids, context=None):
        w_res_company_id = self.pool.get('res.company')._company_default_get(cr, uid, object='res.company', field='property_account_payable', context=context)
        br_res_company = self.pool.get('res.company').browse(cr, uid, w_res_company_id, context=context)
        return br_res_company.partner_default_fiscal_type_id.id

    def create(self, cr, uid, vals, context=None):
        if 'parent_id' in vals:
            if vals['parent_id']:
                vals.update({'customer': False,
                 'supplier': False})
        return super(res_partner, self).create(cr, uid, vals, context=context)

    _defaults = {
        'property_account_payable': _get_account_payable,
        'property_account_receivable': _get_account_receivable,
        'partner_fiscal_type_id': _get_fiscal_type
    }


res_partner()
