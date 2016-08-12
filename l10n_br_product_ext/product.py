# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_product_ext/product.py
from openerp.osv import osv, fields

class product_product(osv.osv):
    _inherit = 'product.product'

    def name_get(self, cr, user, ids, context = None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        else:

            def _name_get(d):
                name = d.get('name', '')
                code = d.get('default_code', False)
                if code:
                    name = '[%s] %s' % (code, name)
                return (d['id'], name)

            partner_id = context.get('partner_id', False)
            result = []
            for product in self.browse(cr, user, ids, context=context):
                sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
                if sellers:
                    for s in sellers:
                        mydict = {'id': product.id,
                         'name': s.product_name or product.name,
                         'default_code': s.product_code or product.default_code,
                         'variants': product.variants}
                        result.append(_name_get(mydict))

                else:
                    mydict = {'id': product.id,
                     'name': product.name,
                     'default_code': product.default_code,
                     'variants': product.variants}
                    result.append(_name_get(mydict))

            return result