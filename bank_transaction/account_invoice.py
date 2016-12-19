# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, date
from osv import osv, fields
from openerp.osv import osv, fields
from pyboleto.pdf import BoletoPDF
from pyboleto.bank.itau import BoletoItau
from decimal import Decimal
from string import replace


class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    _columns = {
        'date_last_payment': fields.date(u'Data último pagamento'),
    }

    def confirm_paid(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).confirm_paid(
            cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'date_last_payment': datetime.now()}, context=context)
        return res

    def payment_type_default(self, cr, uid, result, False, partner_id,
                             company_id, context=None):
        obj_res_partner = self.pool.get('res.partner')
        br_res_partner = obj_res_partner.browse(
            cr, uid, partner_id, context=context)
        for rec_payment_type_default in br_res_partner.payment_type_default:
            if company_id == rec_payment_type_default.company_id.id:
                result['value']['payment_type'] = \
                    rec_payment_type_default.payment_type.id
                return result

        return result

    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type,
                            invoice_line, currency_id,
                            fiscal_category_id=False):
        result = super(account_invoice, self).onchange_company_id(
            cr, uid, ids, company_id, partner_id, type,
            invoice_line, currency_id)
        return self.payment_type_default(
            cr, uid, result, False, partner_id=partner_id,
            company_id=company_id)

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):
        result = super(account_invoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)
        return self.payment_type_default(
            cr, uid, result, False, partner_id=partner_id,
            company_id=company_id)
