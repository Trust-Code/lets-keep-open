# Embedded file name: /home/ubuntu/workspace/openerp7-base/addons-extra/l10n_br_cnab_base/bank_receivable.py
import time
import netsvc
from tools.translate import _
from osv import osv, fields
FORMAT_TYPES = ('Arquivo-Remessa', 'Arquivo-Retorno')

class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    def _payment_slip_get(self, cr, uid, ids, field_name, arg, context = {}):
        return self.pool.get('payment.type').browse(cr, uid, context[self.payment_type]).bank_id

    _columns = {'status': fields.selection([('draft', 'Unbalanced'), ('valid', 'Balanced')], 'Status', readonly=True)}