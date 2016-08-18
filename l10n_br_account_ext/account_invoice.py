# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields, osv, expression
from openerp.addons import decimal_precision as dp
import datetime

def first_day_of_month(w_strdate):
    w_date = datetime.datetime.strptime(w_strdate, '%Y-%m-%d')
    w_date_ret = datetime.date(w_date.year, w_date.month, 1)
    return w_date_ret.strftime('%Y-%m-%d')


def last_day_of_month(w_strdate):
    w_date = datetime.datetime.strptime(w_strdate, '%Y-%m-%d')
    if w_date.month == 12:
        w_date_ret = datetime.date(w_date.year, 12, 31)
    else:
        w_date_ret = datetime.date(w_date.year, w_date.month + 1, 1) - datetime.timedelta(days=1)
    return w_date_ret.strftime('%Y-%m-%d')


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def _get_receivable_lines(self, cr, uid, ids, name, arg, context = None):
        res = super(account_invoice, self)._get_receivable_lines(cr, uid, ids, name, arg, context=None)
        most_date = False
        for account_move_line_id in res[ids[0]]:
            date_maturity = self.pool.get('account.move.line').browse(cr, uid, account_move_line_id).date_maturity
            if date_maturity > most_date:
                most_date = date_maturity

        if most_date:
            if most_date > self.browse(cr, uid, ids[0]).date_due:
                self.write(cr, uid, ids[0], {'date_due': most_date})
        return res

    _columns = {
        'immediate_pay_amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'immediate_pay_journal_id': fields.many2one('account.journal', 'Journal', readonly=True, states={'draft': [('readonly', False)]}),
        'move_line_receivable_id': fields.function(_get_receivable_lines, method=True, type='many2many', relation='account.move.line', string='Entry Lines')
    }

    def immediate_payment(self, cr, uid, ids, context = None):
        if not context:
            context = {}
        account_voucher_ids = []
        for rec_account_invoice in self.browse(cr, uid, ids, context=context):
            if not rec_account_invoice.immediate_pay_amount or not rec_account_invoice.immediate_pay_journal_id:
                return True
            context.update({'company_id': rec_account_invoice.company_id.id})
            context.update({'invoice_id': rec_account_invoice.id})
            w_period_ids = self.pool.get('account.period').find(cr, uid, context=context)
            if rec_account_invoice.immediate_pay_journal_id.currency:
                w_currency_id = rec_account_invoice.immediate_pay_journal_id.currency_id.id
            else:
                w_currency_id = rec_account_invoice.company_id.currency_id.id
            account_voucher_vals = {
                'type': 'receipt',
                'name': rec_account_invoice.reference,
                'date': rec_account_invoice.date_invoice,
                'journal_id': rec_account_invoice.immediate_pay_journal_id.id,
                'account_id': rec_account_invoice.immediate_pay_journal_id.default_credit_account_id.id,
                'period_id': w_period_ids and w_period_ids[0] or False,
                'currency_id': w_currency_id,
                'company_id': rec_account_invoice.company_id.id,
                'amount': rec_account_invoice.immediate_pay_amount,
                'reference': 'Imediate Payment',
                'partner_id': rec_account_invoice.partner_id.id
            }
            br_account_voucher = self.pool.get('account.voucher')
            br_account_voucher_line = self.pool.get('account.voucher.line')
            voucher_lines = br_account_voucher.recompute_voucher_lines(cr, uid, ids, account_voucher_vals['partner_id'], account_voucher_vals['journal_id'], account_voucher_vals['amount'], account_voucher_vals['currency_id'], account_voucher_vals['type'], account_voucher_vals['date'], context=context)
            account_voucher_id = br_account_voucher.create(cr, uid, account_voucher_vals, context=context)
            for w_voucher_line in voucher_lines['value']['line_cr_ids']:
                w_voucher_line['voucher_id'] = account_voucher_id
                voucher_line_id = br_account_voucher_line.create(cr, uid, w_voucher_line, context=context)

            account_voucher_ids.append(account_voucher_id)
            br_account_voucher.button_proforma_voucher(cr, uid, account_voucher_ids, context=context)

        return True


account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def move_line_get(self, cr, uid, invoice_id, context = None):
        res = []
        tax_obj = self.pool.get('account.tax')
        tax_code_obj = self.pool.get('account.tax.code')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        for line in inv.invoice_line:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0), line.quantity, line.product_id, inv.partner_id)['taxes']:
                if tax['base_code_id']:
                    tax_code = tax_code_obj.browse(cr, uid, tax['base_code_id'], context=context)
                    if tax_code:
                        if tax_code.account_collected_deduct_id or tax_code.tax_retain_type != 'no_retain':
                            mres['price'] += tax['amount']

            res.append(mres)

        return res

    def _fiscal_position_map(self, cr, uid, result, context = None, **kwargs):
        if not context:
            context = {}
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})
        if not isinstance(result, dict):
            result = {}
        if 'value' not in result:
            result['value'] = {}
        result['value']['cfop_id'] = False
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        result_rule = obj_fp_rule.apply_fiscal_mapping(cr, uid, result, **kwargs)
        if result['value'].get('fiscal_position', False):
            obj_fp = self.pool.get('account.fiscal.position').browse(cr, uid, result['value'].get('fiscal_position', False))
            result_rule['value']['cfop_id'] = obj_fp.cfop_id and obj_fp.cfop_id.id or False
            if kwargs.get('product_id', False):
                obj_product = self.pool.get('product.product').browse(cr, uid, kwargs.get('product_id', False), context=context)
                context['fiscal_type'] = obj_product.fiscal_type
                if context.get('type') in ('out_invoice', 'out_refund'):
                    context['type_tax_use'] = 'sale'
                    taxes = obj_product.taxes_id and obj_product.taxes_id or kwargs.get('account_id', False) and self.pool.get('account.account').browse(cr, uid, kwargs.get('account_id', False), context=context).tax_ids or False
                else:
                    context['type_tax_use'] = 'purchase'
                    taxes = obj_product.supplier_taxes_id and obj_product.supplier_taxes_id or kwargs.get('account_id', False) and self.pool.get('account.account').browse(cr, uid, kwargs.get('account_id', False), context=context).tax_ids or False
                tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, obj_fp, taxes, context)
                result_rule['value']['invoice_line_tax_id'] = tax_ids
                result['value'].update(self._get_tax_codes(cr, uid, kwargs.get('product_id'), obj_fp, tax_ids, kwargs.get('company_id'), context=context))
        return result_rule


account_invoice_line()


class account_invoice_tax(osv.osv):
    _name = 'account.invoice.tax'
    _inherit = 'account.invoice.tax'
    _columns = {
        'tax_retain': fields.float(
            'Tax Retain', digits_compute=dp.get_precision('Account'),
            readonly=True)
    }

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = super(account_invoice_tax, self).compute(cr, uid, invoice_id, context=None)
        obj_account_invoice = self.pool.get('account.invoice')
        obj_account_invoice_tax = self.pool.get('account.invoice.tax')
        rec_account_invoice = obj_account_invoice.browse(cr, uid, invoice_id, context=context)
        w_date_now = datetime.datetime.now()
        w_strdate_now = w_date_now.strftime('%Y-%m-%d')
        src_account_invoice_mnt = obj_account_invoice.search(cr, uid, [('partner_id', '=', rec_account_invoice.partner_id.id),
         ('state', '=', 'open'),
         ('type', '=', 'out_invoice'),
         ('date_invoice', '>=', first_day_of_month(rec_account_invoice.date_invoice or w_strdate_now)),
         ('date_invoice', '<=', last_day_of_month(rec_account_invoice.date_invoice or w_strdate_now))], context=context)
        w_amount_inv_mnt = 0
        for rec_account_invoice_mnt in obj_account_invoice.browse(cr, uid, src_account_invoice_mnt, context=context):
            w_amount_inv_mnt += rec_account_invoice_mnt.amount_total

        w_amount_inv_mnt += rec_account_invoice.amount_total
        for tg_line in tax_grouped:
            if tg_line[0]:
                obj_account_tax_code = self.pool.get('account.tax.code')
                br_account_tax_code = obj_account_tax_code.browse(cr, uid, tg_line[0], context=context)
                key = (tg_line[0],
                 tg_line[1],
                 tg_line[2],
                 tg_line[3])
                tax_grouped[key]['tax_retain'] = 0
                w_tax_retain = 0
                if br_account_tax_code.tax_retain_type == 'by_invoice':
                    if rec_account_invoice.amount_total > br_account_tax_code.tax_retain_amount:
                        w_amount_total = rec_account_invoice.amount_total
                        w_tax_retain = tax_grouped[key]['amount']
                elif br_account_tax_code.tax_retain_type == 'inv_amount_monthly':
                    if w_amount_inv_mnt > br_account_tax_code.tax_retain_amount:
                        src_account_invoice_tax = obj_account_invoice_tax.search(cr, uid, [('invoice_id', 'in', src_account_invoice_mnt), ('tax_code_id', '=', tg_line[0])], context=context)
                        w_tax_no_retain_mnt = 0
                        for rec_account_invoice_tax in obj_account_invoice_tax.browse(cr, uid, src_account_invoice_tax, context=context):
                            w_tax_no_retain_mnt += rec_account_invoice_tax.amount - rec_account_invoice_tax.tax_retain

                        w_tax_retain = w_tax_no_retain_mnt + tax_grouped[key]['amount']
                tax_grouped[key]['tax_retain'] = w_tax_retain

        return tax_grouped

    def move_line_get(self, cr, uid, invoice_id):
        res = []
        for atl in self.pool.get('account.invoice').browse(cr, uid, invoice_id).tax_line:
            if not atl.amount or not atl.tax_code_id or not atl.tax_amount:
                continue
            if atl.tax_retain > 0:
                res.append({
                    'type': 'taxret',
                    'name': atl.name,
                    'price_unit': atl.tax_retain * -1,
                    'quantity': 1,
                    'price': atl.tax_retain * -1 or 0.0,
                    'account_id': atl.tax_code_id.invoice_tax_retain_account.id,
                    'tax_code_id': atl.tax_code_id.id,
                    'tax_amount': atl.tax_amount,
                    'account_analytic_id': atl.account_analytic_id.id
                })
            else:
                res.append({
                    'type': 'tax',
                    'name': atl.name,
                    'price_unit': atl.amount,
                    'quantity': 1,
                    'price': atl.amount or 0.0,
                    'account_id': atl.account_id.id,
                    'tax_code_id': atl.tax_code_id.id,
                    'tax_amount': atl.tax_amount,
                    'account_analytic_id': atl.account_analytic_id.id
                })
                if atl.tax_code_id.account_collected_deduct_id:
                    res.append(
                        {'type': 'tax',
                         'name': atl.name,
                         'price_unit': atl.amount * -1,
                         'quantity': 1,
                         'price': atl.amount * -1 or 0.0,
                         'account_id': atl.tax_code_id.account_collected_deduct_id.id,
                         'account_analytic_id': atl.account_analytic_id.id})

        return res


account_invoice_tax()
