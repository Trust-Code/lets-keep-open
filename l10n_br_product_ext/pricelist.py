# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv

class product_pricelist_item(osv.osv):
    _inherit = 'product.pricelist.item'
    _columns = {'ipd': fields.float('IPD', digits=(16, 4))}


product_pricelist_item()
