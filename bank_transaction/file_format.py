# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from tools.translate import _
from osv import osv, fields
from datetime import datetime, date


class FileFormat(osv.osv):
    _name = 'cnab.file_format'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'version': fields.char('Version', size=256),
        'description': fields.text('Description'),
        'records_ids': fields.one2many('cnab.record_format', 'file_id',
                                       'Records'),
        'type': fields.selection(
            [('remessa', 'Arquivo de Remessa Bancária'),
             ('retorno', 'Arquivo de Retorno Bancário'),
             ('extrato', 'Arquivo de Extrato Bancário')],
            'File Type', required=True),
        'bank': fields.many2one('res.bank', 'Bank'),
        'filename': fields.char('Filename')
    }


class RecordFormat(osv.osv):
    _name = 'cnab.record_format'

    def _get_id(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        obj_cnab_field_format = self.pool.get('cnab.field_format')
        for recordformat in self.browse(cr, uid, ids):
            src_cnab_field_format = obj_cnab_field_format.search(
                cr, uid, [('type', '=', 'IdType'),
                          ('record_id', '=', recordformat.id)], context=None)
            br_cnab_field_format = obj_cnab_field_format.browse(
                cr, uid, src_cnab_field_format[0], context=None)
            res[recordformat.id] = br_cnab_field_format.value

        return res

    _columns = {
        'file_id': fields.many2one('cnab.file_format', 'File'),
        'record_id': fields.many2one('cnab.record_format', 'Parent Record'),
        'identifier': fields.function(_get_id, method=True, type='char',
                                      string='IdType'),
        'name': fields.char('Name', size=256),
        'description': fields.char('Description', size=256),
        'repeatable': fields.boolean('repeatable'),
        'records_ids': fields.one2many('cnab.record_format', 'record_id',
                                       'Inner Records'),
        'fields_ids': fields.one2many('cnab.field_format', 'record_id',
                                      'Fields')
    }


class FieldFormat(osv.osv):
    _name = 'cnab.field_format'
    VALID_TYPES = ('STRING', 'CHARACTER', 'INTEGER', 'DATE', 'BIGDECIMAL')
    VALID_FORMATS = ('DATE_DDMMYY', 'DECIMAL_DD')
    VALID_PADDINGS = ('ZERO_LEFT',)
    InternalTypes = ('IdType', 'Field', 'SequencialNumber')
    _columns = {
        'record_id': fields.many2one('cnab.record_format', 'Record'),
        'sequence': fields.integer('Sequence'),
        'type': fields.selection(zip(InternalTypes, InternalTypes), 'Type'),
        'name': fields.char('Name', size=256),
        'value': fields.char('Value', size=256),
        'length': fields.integer('Length'),
        'position': fields.integer('Position'),
        'value_type': fields.selection(zip(VALID_TYPES, VALID_TYPES),
                                       'Value Type'),
        'format': fields.selection(zip(VALID_FORMATS, VALID_FORMATS),
                                   'Format'),
        'padding': fields.selection(zip(VALID_PADDINGS, VALID_PADDINGS),
                                    'Padding')
    }
    _order = 'sequence'
