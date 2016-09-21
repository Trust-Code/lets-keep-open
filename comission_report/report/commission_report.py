# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from openerp.report import report_sxw
from openerp import pooler
from openerp import tools
from openerp.osv import fields, osv


class commission_report(report_sxw.rml_parse):
    _name = 'commission.report'
    _description = 'Contract Partner Commission Report'

    def __init__(self, cr, uid, name, context):
        super(commission_report, self).__init__(cr, uid, name, context=context)


report_sxw.report_sxw('report.commission.report',
                      'res.partner',
                      'addons/comission_report/report/commission.mako',
                      parser=commission_report)
