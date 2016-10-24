# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import datetime
from openerp.osv import osv, fields
from openerp.addons.decimal_precision import decimal_precision as dp
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def _ca_invoiced_calc(self, cr, uid, ids, name, arg, context = None):
        res = {}
        res_final = {}
        child_ids = tuple(ids)
        for i in child_ids:
            res[i] = 0.0

        if not child_ids:
            return res
        if child_ids:
            inv_line_obj = self.pool.get('account.invoice.line')
            inv_lines = inv_line_obj.search(
                cr, uid, ['&', ('account_analytic_id', 'in', child_ids),
                          ('invoice_id.state', '!=', 'cancel')],
                context=context)
            for line in inv_line_obj.browse(cr, uid, inv_lines, context=context):
                res[line.account_analytic_id.id] += line.price_total

        for acc in self.browse(cr, uid, res.keys(), context=context):
            res[acc.id] = res[acc.id] - (acc.timesheet_ca_invoiced or 0.0)

        res_final = res
        return res_final

    _columns = {
        'ca_invoiced': fields.function(_ca_invoiced_calc, type='float', string='Invoiced Amount', help='Total customer invoiced amount for this account.', digits_compute=dp.get_precision('Account')),
        'date_cancel': fields.date('Cancel Date'),
        'months_renewal': fields.integer('Months to renewal', help='Months to next due date'),
        'res_currency_id': fields.many2one('res.currency', 'Rate to renewal'),
        'generate_invoice_parent': fields.boolean('Generate Invoices for Parent Contract'),
        'grouping_invoice_parent': fields.boolean('Grouping Invoice in Parent Contract'),
        'recurring_rule_type': fields.selection(
            [('daily', 'Day(s)'),
             ('weekly', 'Week(s)'),
             ('monthly', 'Month(s)'),
             ('yearly', 'Year(s)')], 'Recurrency',
            help='Invoice automatically repeat at specified interval'),
        'recurring_interval': fields.integer(
            'Repeat Every', help='Repeat every (Days/Week/Month/Year)'),
        'recurring_next_date': fields.date('Date of Next Invoice'),
        'fiscal_type': fields.selection(
            [('product', 'Produto'),
             ('service', 'Serviço')], 'Fiscal Type', required=False),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
        'recurring_invoice_line_ids': fields.one2many(
            'account.analytic.invoice.line', 'analytic_account_id', 'Invoice Lines'),
        'invoice_additem_ids': fields.one2many(
            'account.analytic.additional.item', 'analytic_account_id', 'Additional Item'),
        'special_condition_ids': fields.one2many(
            'account.analytic.special.condition', 'analytic_account_id', 'Special Condition'),
        'salesperson_id': fields.many2one('res.users', 'Salesperson'),
        'salesperson_commission': fields.float('Salesperson Commission (%)'),
        'partner_commission_ids': fields.one2many(
            'account.analytic.partner.commission', 'analytic_account_id',
            'Partner Commission'),
        'stock_production_lot_ids': fields.one2many(
            'stock.production.lot', 'analytic_account_id', 'Serial Number')
    }

    _defaults = {
        'recurring_interval': 1,
        'recurring_next_date': lambda *a: time.strftime('%Y-%m-%d'),
        'recurring_rule_type': 'monthly'
    }

    def action_create_invoice(self, cr, uid, ids, limit_date=None, context=None):
        for rec_contract in self.browse(cr, uid, ids, context=context):
            if not rec_contract.grouping_invoice_parent:
                w_recurring_next_date = rec_contract.recurring_next_date
                contract_end_date = rec_contract.date or w_recurring_next_date
                while w_recurring_next_date <= limit_date and w_recurring_next_date <= contract_end_date:
                    self.create_invoice(cr, uid, rec_contract, w_recurring_next_date, context=context)
                    w_recurring_next_date = self.get_next_date_invoice(cr, uid, rec_contract, w_recurring_next_date, context=context)
                    self.write(cr, uid, [rec_contract.id], {'recurring_next_date': w_recurring_next_date}, context=context)

    def get_next_date_invoice(self, cr, uid, rec_contract, invoice_date, context = None):
        context = context or {}
        next_date = datetime.datetime.strptime(invoice_date, '%Y-%m-%d')
        interval = rec_contract.recurring_interval or 1
        if rec_contract.recurring_rule_type == 'daily':
            new_date = next_date + relativedelta(days=+interval)
        elif rec_contract.recurring_rule_type == 'weekly':
            new_date = next_date + relativedelta(weeks=+interval)
        else:
            new_date = next_date + relativedelta(months=+interval)
        return new_date.strftime('%Y-%m-%d')

    def create_invoice(self, cr, uid, rec_contract, invoice_date, context = None):
        context = context or {}
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        contract_obj = self.pool.get('account.analytic.account')
        if rec_contract.generate_invoice_parent and rec_contract.parent_id != False:
            rec_partner = rec_contract.parent_id.partner_id
        else:
            rec_partner = rec_contract.partner_id
        if not rec_partner:
            raise osv.except_osv(_('No Customer Defined!'),
                                 _('You must first select a Customer for Contract %s!') % rec_contract.name)
        if rec_contract.fiscal_type == 'service':
            fcateg = rec_contract.company_id.out_invoice_service_fiscal_category_id.id
        else:
            fcateg = rec_contract.company_id.out_invoice_fiscal_category_id.id
        fpos = rec_partner.property_account_position or False
        journal_ids = journal_obj.search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', rec_contract.company_id.id or False)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'), _('Please define a sale journal for the company "%s".') % (rec_contract.company_id.name or '',))
        salesperson = False
        section = False
        if rec_contract.salesperson_id:
            salesperson = rec_contract.salesperson_id.id
            section = rec_contract.salesperson_id.default_section_id.id
        inv_data = {
            'reference': rec_contract.code or False,
            'account_id': rec_partner.property_account_receivable.id or False,
            'type': 'out_invoice',
            'partner_id': rec_partner.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'date_invoice': invoice_date,
            'origin': rec_contract.name,
            'payment_term': False,
            'payment_type': rec_partner.payment_type_customer.id or False,
            'company_id': rec_contract.company_id.id or False,
            'fiscal_type': rec_contract.fiscal_type,
            'fiscal_category_id': fcateg,
            'fiscal_position': False,
            'user_id': salesperson,
            'section_id': section,
            'currency_id': rec_contract.company_id.currency_id.id or False
        }
        kwargs = {
            'partner_id': rec_partner.id,
            'partner_invoice_id': rec_partner.id,
            'fiscal_category_id': fcateg,
            'company_id': rec_contract.company_id.id or False,
            'context': context
        }
        inv_add_data = self.pool.get('account.fiscal.position.rule').apply_fiscal_mapping(cr, uid, {'value': inv_data}, **kwargs)
        inv_data['fiscal_position'] = inv_add_data['value'].get('fiscal_position')
        lst_payment_term = {}
        w_payment_term_parent = 0
        additem_valid = False
        for additem_obj in rec_contract.invoice_additem_ids:
            if additem_obj.invoice_date_planned <= rec_contract.recurring_next_date and not additem_obj.invoice_date:
                additem_valid = True

        if len(rec_contract.recurring_invoice_line_ids) > 0 or additem_valid:
            contract_start_date = rec_contract.date_start or rec_contract.recurring_next_date
            contract_end_date = rec_contract.date or rec_contract.recurring_next_date
            if rec_contract.recurring_next_date >= rec_contract.date_start and rec_contract.recurring_next_date <= contract_end_date and rec_contract.state == 'open':
                for spe_conditions in rec_contract.special_condition_ids:
                    if rec_contract.recurring_next_date >= spe_conditions.start_date and rec_contract.recurring_next_date <= spe_conditions.end_date:
                        w_payment_term_parent = spe_conditions.payment_term.id

                if w_payment_term_parent == 0:
                    w_payment_term_parent = rec_contract.payment_term_id and rec_contract.payment_term_id.id or 0
                if w_payment_term_parent == 0:
                    w_payment_term_parent = rec_partner.property_payment_term and rec_partner.property_payment_term.id or 0
                lst_payment_term[w_payment_term_parent] = [rec_contract.id]
        for rec_contract_child in rec_contract.child_complete_ids:
            if rec_contract_child.grouping_invoice_parent and rec_contract_child.state == 'open':
                additem_valid = False
                for additem_obj in rec_contract_child.invoice_additem_ids:
                    if additem_obj.invoice_date_planned <= rec_contract.recurring_next_date and not additem_obj.invoice_date:
                        additem_valid = True

                if len(rec_contract_child.recurring_invoice_line_ids) > 0 or additem_valid:
                    w_payment_term_id = 0
                    contract_start_date = rec_contract_child.date_start or rec_contract_child.recurring_next_date
                    contract_end_date = rec_contract_child.date or rec_contract_child.recurring_next_date
                    if rec_contract.recurring_next_date >= contract_start_date and rec_contract.recurring_next_date <= contract_end_date:
                        for spe_conditions in rec_contract_child.special_condition_ids:
                            if rec_contract_child.recurring_next_date >= spe_conditions.start_date and rec_contract_child.recurring_next_date <= spe_conditions.end_date:
                                w_payment_term_id = spe_conditions.payment_term.id

                        if w_payment_term_id == 0:
                            w_payment_term_id = rec_contract_child.payment_term_id.id or w_payment_term_parent
                        if w_payment_term_id not in lst_payment_term:
                            lst_payment_term[w_payment_term_id] = []
                        lst_payment_term[w_payment_term_id].append(rec_contract_child.id)

        for w_payment_term in lst_payment_term:
            inv_data['payment_term'] = w_payment_term
            invoice_id = inv_obj.create(cr, uid, inv_data, context=context)
            for contract in contract_obj.browse(cr, uid, lst_payment_term[w_payment_term], context=context):
                w_discount = 0
                for spe_conditions in contract.special_condition_ids:
                    if rec_contract.recurring_next_date >= spe_conditions.start_date and rec_contract.recurring_next_date <= spe_conditions.end_date:
                        w_discount = spe_conditions.discount

                for inv_line in contract.recurring_invoice_line_ids:
                    if invoice_date < inv_line.inactive_date or not inv_line.inactive_date:
                        self.create_line(cr, uid, invoice_id, contract, rec_contract, inv_line, inv_data, w_discount, fpos, context=None)

                for inv_line in contract.invoice_additem_ids:
                    if inv_line.invoice_date_planned <= rec_contract.recurring_next_date and not inv_line.invoice_date:
                        self.create_line(cr, uid, invoice_id, contract, rec_contract, inv_line, inv_data, w_discount, fpos, context=None)
                        self.pool.get('account.analytic.additional.item').write(cr, uid, [inv_line.id], {'invoice_date': rec_contract.recurring_next_date}, context=context)

        return

    def create_line(self, cr, uid, invoice_id, contract, contract_parent, inv_line, inv_data, discount, fpos, context = None):
        fpos_obj = self.pool.get('account.fiscal.position')
        product = inv_line.product_id
        account_id = product.property_account_income.id
        if not account_id:
            account_id = product.categ_id.property_account_income_categ.id
        account_id = fpos_obj.map_account(cr, uid, fpos, account_id)
        taxes = product.taxes_id or False
        w_fiscal_position = inv_data.get('fiscal_position') or False
        tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)
        if not w_fiscal_position:
            cfop_id = False
        else:
            cfop_id = fpos_obj.browse(cr, uid, w_fiscal_position).cfop_id.id
        invoice_line_val = {
            'name': product.name,
            'account_id': account_id,
            'account_analytic_id': contract.id,
            'price_unit': inv_line.price_unit or 0.0,
            'quantity': inv_line.quantity,
            'uos_id': product.uom_id.id or False,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
            'invoice_line_tax_id': [(6, 0, tax_id)],
            'fiscal_category_id': inv_data.get('fiscal_category_id'),
            'product_type': contract_parent.fiscal_type,
            'fiscal_classification_id': product.property_fiscal_classification.id,
            'fiscal_position': inv_data.get('fiscal_position'),
            'cfop_id': cfop_id,
            'discount': discount
        }
        self.pool.get('account.invoice.line').create(
            cr, uid, invoice_line_val, context=context)

    def set_cancel(self, cr, uid, ids, context=None):
        return self.write(
            cr, uid, ids, {
                'state': 'cancelled',
                'date_cancel': datetime.date.today()}, context=context)

    def set_open(self, cr, uid, ids, context=None):
        return self.write(
            cr, uid, ids, {
                'state': 'open',
                'date_cancel': False}, context=context)


account_analytic_account()


class account_analytic_invoice_line(osv.osv):
    _name = 'account.analytic.invoice.line'
    _description = 'Contract Invoice Line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.quantity * line.price_unit

        return res

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'quantity': fields.float('Quantity', required=True),
        'price_unit': fields.float('Unit Price', required=True),
        'price_subtotal': fields.function(_amount_line, string='Sub Total', type='float', digits_compute=dp.get_precision('Account')),
        'inactive_date': fields.date('Inactive Date')
    }
    _defaults = {'quantity': 1}

    def product_id_change(self, cr, uid, ids, product=None, partner_id=None, context=None):
        uom_id = False
        result = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, product, uom_id, partner_id=partner_id)
        return result

    def subtotal_change(self, cr, uid, ids, quantity, price_unit, context = None):
        return {'value': {'price_subtotal': quantity * price_unit}}


account_analytic_invoice_line()


class account_analytic_additional_item(osv.osv):
    _name = 'account.analytic.additional.item'
    _description = 'Contract Additional Items'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict, context = None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.quantity * line.price_unit

        return res

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'quantity': fields.float('Quantity', required=True),
        'price_unit': fields.float('Unit Price', required=True),
        'price_subtotal': fields.function(_amount_line, string='Sub Total', type='float', digits_compute=dp.get_precision('Account')),
        'invoice_date_planned': fields.date('Invoice Date Planned'),
        'invoice_date': fields.date('Invoice Date', readonly=True)
    }
    _defaults = {'quantity': 1}

    def product_id_change(self, cr, uid, ids, product = None, partner_id = None, context = None):
        uom_id = False
        result = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, product, uom_id, partner_id=partner_id)
        return result

    def subtotal_change(self, cr, uid, ids, quantity, price_unit, context = None):
        return {'value': {'price_subtotal': quantity * price_unit}}


account_analytic_invoice_line()


class account_analytic_special_condition(osv.osv):
    _name = 'account.analytic.special.condition'
    _description = 'Contract Special Condition'
    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'start_date': fields.date('Start Date'),
        'end_date': fields.date('End Date'),
        'discount': fields.float('Discount (%)'),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term')
    }


account_analytic_special_condition()


class account_analytic_partner_commission(osv.osv):
    _name = 'account.analytic.partner.commission'
    _description = 'Contract Partner Commission'
    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_commission': fields.float('Partner Commission (%)', required=True)
    }


account_analytic_partner_commission()
