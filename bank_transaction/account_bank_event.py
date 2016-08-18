# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from osv import osv, fields
from openerp.osv import osv, fields

class account_bank_event(osv.osv):
    _name = 'account.bank.event'
    _columns = {
        'bank_id': fields.many2one('res.bank', 'Bank', required=True),
        'action': fields.selection(
            [('pay', 'Pay'), ('confirm', 'Confirm')], 'Action', required=True),
        'code_occurrence': fields.char('Code Occurrence', required=True)
    }
    _defaults = {}
