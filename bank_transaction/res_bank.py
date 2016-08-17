# Embedded file name: /opt/openerp/producao/addons-extra/bank_transaction/res_bank.py

from tools.translate import _
from osv import osv, fields


class Bank(osv.osv):
    _name = 'res.bank'
    _inherit = 'res.bank'
    _columns = {
        'code_occurrence_ids': fields.one2many(
            'account.bank.event', 'bank_id', 'Codes of Occurrence')
    }
