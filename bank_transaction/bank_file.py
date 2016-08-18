# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, date
from osv import osv, fields
from openerp.osv import osv, fields
from pyboleto.pdf import BoletoPDF
from pyboleto.bank.itau import BoletoItau


class account_bank_file(osv.osv):
    _name = 'account.bank.file'
    _order = 'date_time desc'
    _columns = {
        'file_type': fields.selection([('remessa', 'Remessa'),
                                       ('retorno', 'Retorno'),
                                       ('extrato', 'Extrato')],
                                      'File Type', required=True),
        'bank': fields.many2one('res.bank', 'Bank'),
        'filename': fields.char('Filename', size=128),
        'date_time': fields.datetime('Date/Time'),
        'cnab_file': fields.binary('CNAB File')
    }
    _defaults = {'filename': 'CNAB.txt'}
