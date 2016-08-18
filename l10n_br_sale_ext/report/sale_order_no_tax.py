# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from openerp.report import report_sxw

class order_no_tax(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context = None):
        super(order_no_tax, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'show_discount': self._show_discount})

    def _show_discount(self, uid, context = None):
        cr = self.cr
        try:
            group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'group_discount_per_so_line')[1]
        except:
            return False

        return group_id in [ x.id for x in self.pool.get('res.users').browse(cr, uid, uid, context=context).groups_id ]


report_sxw.report_sxw('report.sale.order.no.tax', 'sale.order', 'l10n_br_sale_ext/report/sale_order_no_tax.rml', parser=order_no_tax, header='external')
