# Embedded file name: /home/ubuntu/wspace_openerp/openerp-extra/addons-extension/l10n_br_sale_ext/sale.py
from openerp.osv import orm, fields
from openerp.osv import fields, osv
from openerp.addons import decimal_precision as dp
from openerp.tools.translate import _

class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _default_fiscal_document(self, cr, uid, context):
        rec_res_user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return rec_res_user.company_id.product_invoice_id.id or False

    _columns = {'fiscal_document_id': fields.many2one('l10n_br_account.fiscal.document', 'Fiscal Document', readonly=True, states={'draft': [('readonly', False)]}),
     'immediate_pay_amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
     'immediate_pay_journal_id': fields.many2one('account.journal', 'Journal', readonly=True, states={'draft': [('readonly', False)]})}
    _defaults = {'fiscal_document_id': _default_fiscal_document}

    def onchange_shop_id(self, cr, uid, ids, shop_id = None, context = None, partner_id = None, partner_invoice_id = None, partner_shipping_id = None, fiscal_category_id = None, **kwargs):
        new_value = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, context, partner_id, partner_invoice_id, partner_shipping_id, fiscal_category_id=fiscal_category_id)
        context.update({'shop_id': shop_id})
        w_fiscal_category_id = self._default_fiscal_category(cr, uid, context)
        if w_fiscal_category_id:
            new_value['value']['fiscal_category_id'] = w_fiscal_category_id
        return new_value

    def _prepare_invoice(self, cr, uid, order, lines, context = None):
        result = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        w_fiscal_position = order.fiscal_position or order.partner_id.property_account_position
        w_account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, w_fiscal_position, result['account_id'])
        if w_account_id:
            result['account_id'] = w_account_id
        if order.fiscal_document_id:
            fiscal_document_id = order.fiscal_document_id.id
            result['fiscal_document_id'] = order.fiscal_document_id.id
        elif context.get('fiscal_type') == 'product':
            fiscal_document_id = order.company_id.product_invoice_id.id
        else:
            fiscal_document_id = order.company_id.sevice_invoice_id.id
        issuer = '0'
        ids = False
        result_value = self.pool.get('account.invoice').onchange_fiscal_document_id(cr, uid, ids, fiscal_document_id, order.company_id.id, issuer, context.get('fiscal_type'), context)
        if result_value['value']['document_serie_id']:
            result['document_serie_id'] = result_value['value']['document_serie_id']
        result['immediate_pay_amount'] = order.immediate_pay_amount
        result['immediate_pay_journal_id'] = order.immediate_pay_journal_id.id
        return result


sale_order()

class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def onchange_price_unit(self, cr, uid, ids, pricelist = False, price_unit = 0, product = False, qty = 0, partner_id = False, uom = False, date_order = False, context = None):
        if self.pool.get('ir.model.access').check_groups(cr, uid, 'l10n_br_sale_ext.group_block_price_change'):
            if product:
                w_warning = {}
                w_price_unit_list = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product, qty or 1.0, partner_id, {'uom': uom,
                 'date': date_order})[pricelist]
                if price_unit != w_price_unit_list:
                    w_warning.update({'title': _('Permission Denied'),
                     'message': _('You do not have permission to modify Unit Price !!')})
                    return {'value': {'price_unit': w_price_unit_list},
                     'warning': w_warning}
        return True


sale_order_line()