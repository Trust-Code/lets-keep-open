# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from tools.translate import _
from osv import osv, fields


class Bank(osv.osv):
    _name = 'res.bank'
    _inherit = 'res.bank'
    _columns = {
        'code_occurrence_ids': fields.one2many(
            'account.bank.event', 'bank_id', 'Codes of Occurrence')
    }
