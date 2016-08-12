# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_product_ext/pricelist.py
from openerp.osv import fields, osv

class product_pricelist_item(osv.osv):
    _inherit = 'product.pricelist.item'
    _columns = {'ipd': fields.float('IPD', digits=(16, 4))}


product_pricelist_item()