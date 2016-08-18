# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tools.translate import _
from datetime import datetime
from osv import osv, fields
import logging
import os
TYPE_ADAPTERS = {
    'INTEGER': int,
    'DATE': lambda s: datetime.strptime(s, '%d%m%y').date(),
    'CHARACTER': lambda s: s
}


class CNABParser(object):

    def get_record_formats(self, parent):
        record_formats = dict(((r.identifier, r) for r in parent.records_ids))
        for child_record in parent.records_ids:
            record_formats.update(self.get_record_formats(child_record))

        return record_formats

    def consume_whitespace(self, cnab_file):
        while True:
            c = cnab_file.read(1)
            if c not in '\r\n':
                cnab_file.seek(-1, os.SEEK_CUR)
                return
            if c == '':
                return

    def get_record_format(self, cnab_file, record_formats,
                          format, idtype_length):
        if format.type == 'retorno':
            idtype = cnab_file.read(idtype_length)
            cnab_file.seek(-idtype_length, os.SEEK_CUR)
        elif format.type == 'extrato':
            idtype = cnab_file.read(8)
            if idtype == '':
                return None
            idtype = idtype[7]
            cnab_file.seek(-8, os.SEEK_CUR)
        if idtype == '':
            return None
        else:
            record_format = record_formats[idtype]
            return record_format

    def parse_file(self, format, cnab_file):
        record_formats = self.get_record_formats(format)
        idtype_length = len(format.records_ids[0].identifier)
        records = []
        while True:
            record_format = self.get_record_format(
                cnab_file, record_formats, format, idtype_length)
            if record_format is None:
                break
            records.append(self.parse_record(record_format, cnab_file))
            self.consume_whitespace(cnab_file)

        return records

    def parse_record(self, format, cnab_file):
        record = {}
        for field in format.fields_ids:
            value = cnab_file.read(field.length).strip()
            if value == '':
                value = False
            if value and field.value_type:
                try:
                    adapter = TYPE_ADAPTERS[field.value_type]
                    value = adapter(value)
                except ValueError as e:
                    logging.warn(
                        'ValueError: %s, on field %s %s', repr(e),
                        field.name, field)
                    raise e

            record[field.name] = value

        return record
