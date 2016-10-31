# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from osv import osv, fields


class payment_type(osv.osv):
    _name = 'payment.type'
    _inherit = 'payment.type'
    _columns = {
        'bank_account': fields.many2one('res.partner.bank', 'Bank Account'),
        'layout_remessa': fields.many2one(
            'cnab.file_format', 'Layout de Remessa',
            domain=[('type', '=', 'remessa')]),
        'layout_retorno': fields.many2one(
            'cnab.file_format', 'Layout de Retorno',
            domain=[('type', '=', 'retorno')]),
        'layout_extrato': fields.many2one(
            'cnab.file_format', 'Layout do Extrato',
            domain=[('type', '=', 'extrato')]),
        'type_banking_billing': fields.selection(
            [('REG', 'Registrada'), ('SRG', 'Sem Registro'),
             ('ESC', 'Escritural')], 'Type Banking Billing'),
        'sequence_our_number': fields.many2one(
            'ir.sequence', 'Sequência Nosso Número'),
        'bank_col_service': fields.char('Carteira de Cobrança Bancária', size=3),
    }

payment_type()
