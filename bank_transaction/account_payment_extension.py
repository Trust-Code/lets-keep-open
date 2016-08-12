# Embedded file name: /opt/openerp/producao/addons-extra/bank_transaction/account_payment_extension.py
from osv import osv, fields

class payment_type(osv.osv):
    _name = 'payment.type'
    _inherit = 'payment.type'
    _columns = {'bank_account': fields.many2one('res.partner.bank', 'Bank Account'),
     'layout_remessa': fields.many2one('cnab.file_format', 'Layout de Remessa', domain=[('type', '=', 'remessa')]),
     'layout_retorno': fields.many2one('cnab.file_format', 'Layout de Retorno', domain=[('type', '=', 'retorno')]),
     'layout_extrato': fields.many2one('cnab.file_format', 'Layout do Extrato', domain=[('type', '=', 'extrato')]),
     'type_banking_billing': fields.selection([('REG', 'Registrada'), ('SRG', 'Sem Registro'), ('ESC', 'Escritural')], 'Type Banking Billing')}


payment_type()