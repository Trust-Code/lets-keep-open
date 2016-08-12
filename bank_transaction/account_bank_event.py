# Embedded file name: /opt/openerp/producao/addons-extra/bank_transaction/account_bank_event.py
from osv import osv, fields
from openerp.osv import osv, fields

class account_bank_event(osv.osv):
    _name = 'account.bank.event'
    _columns = {'bank_id': fields.many2one('res.bank', 'Bank', required=True),
     'action': fields.selection([('pay', 'Pay'), ('confirm', 'Confirm')], 'Action', required=True),
     'code_occurrence': fields.char('Code Occurrence', required=True)}
    _defaults = {}