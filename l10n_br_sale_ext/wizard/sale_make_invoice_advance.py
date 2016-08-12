# Embedded file name: /home/ubuntu/wspace_openerp/openerp-extra/addons-extension/l10n_br_sale_ext/wizard/sale_make_invoice_advance.py
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id, False, partner_id=sale.partner_id.id, fposition_id=sale.fiscal_position.id)
            res = val['value']
            if not wizard.product_id.id:
                prop = ir_property_obj.get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'), _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'), _('There is no income account defined for this product: "%s" (id:%d).') % (wizard.product_id.name, wizard.product_id.id))
            if wizard.amount <= 0.0:
                raise osv.except_osv(_('Incorrect Data'), _('The value of Advance Amount must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_total * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = _('Advance of %s %%') % wizard.amount
            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        res['name'] = _('Advance of %s %s') % (inv_amount, symbol)
                    else:
                        res['name'] = _('Advance of %s %s') % (symbol, inv_amount)
            if res.get('invoice_line_tax_id'):
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False
            inv_line_values = {'name': res.get('name'),
             'origin': sale.name,
             'account_id': res['account_id'],
             'price_unit': inv_amount,
             'quantity': wizard.qtty or 1.0,
             'discount': False,
             'uos_id': res.get('uos_id', False),
             'product_id': wizard.product_id.id,
             'invoice_line_tax_id': res.get('invoice_line_tax_id'),
             'account_analytic_id': sale.project_id.id or False}
            inv_values = {'name': sale.client_order_ref or sale.name,
             'origin': sale.name,
             'type': 'out_invoice',
             'reference': False,
             'account_id': sale.partner_id.property_account_receivable.id,
             'partner_id': sale.partner_invoice_id.id,
             'invoice_line': [(0, 0, inv_line_values)],
             'currency_id': sale.pricelist_id.currency_id.id,
             'comment': '',
             'payment_term': sale.payment_term.id,
             'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id}
            result.append((sale.id, inv_values))

        return result


sale_advance_payment_inv()