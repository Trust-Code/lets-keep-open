# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from tools.translate import _
from osv import osv, fields
from collections import OrderedDict
from cStringIO import StringIO
from datetime import datetime
import os
TYPE_ADAPTERS = {
    'INTEGER': unicode,
    'DATE': lambda d: d.strftime('%d%m%y'),
    'CHARACTER': lambda s: s.upper()
}


class CNABGenerator(object):

    def get_record_formats(self, parent):
        record_formats = dict(((r.identifier, r) for r in parent.records_ids))
        for child_record in parent.records_ids:
            record_formats.update(self.get_record_formats(child_record))

        return record_formats

    def pad_value(self, padding, length, value):
        value = str(value)
        if padding == 'ZERO_LEFT':
            value = value.rjust(length, '0')
        else:
            length_value = len(value)
            w_diference = length - length_value
            w_space = ' ' * w_diference
            value = value + w_space
        return value

    def get_record_format(self, cnab_file, record_formats, idtype_length):
        idtype = cnab_file.read(idtype_length)
        cnab_file.seek(-idtype_length, os.SEEK_CUR)
        if idtype == '':
            return None
        else:
            record_format = record_formats[idtype]
            return record_format

    def generate_file(self, format, records):
        try:
            record_formats = self.get_record_formats(format)
            result_file = StringIO()
            for record in records:
                record_format = record_formats[record['IDReg']]
                for field in record_format.fields_ids:
                    self.generate_field(field, record, result_file)

                result_file.write('\r\n')

            result_file.seek(0)
            return result_file
        except:
            raise osv.except_osv(
                _('Error'), _('Erro apresentado no campo %s') % field.name)

    def generate_field(self, field, record, result_file):
        if field.value is False:
            value = record[field.name]
        else:
            value = field.value
        if value is False or value is None:
            value = ''
        if field.value_type:
            adapter = TYPE_ADAPTERS[field.value_type]
            value = adapter(value)
        value = value[:field.length]
        value = self.pad_value(field.padding, field.length, value)
        result_file.write(value)
        return
