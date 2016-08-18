# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import netsvc
import logging
import base64
import re
import pytz
from datetime import datetime, date
from tools.translate import _
from osv import osv, fields
from decimal import Decimal, Context, Inexact
from itertools import count
from generator import CNABGenerator


def counter(start=0):
    try:
        return count(start=start)
    except TypeError:
        c = count()
        c.next()
        return c


if hasattr(Decimal, 'from_float'):
    float_to_decimal = Decimal.from_float
else:

    def float_to_decimal(f):
        """Convert a floating point number to a Decimal with no loss"""
        n, d = f.as_integer_ratio()
        numerator, denominator = Decimal(n), Decimal(d)
        ctx = Context(prec=60)
        result = ctx.divide(numerator, denominator)
        while ctx.flags[Inexact]:
            ctx.flags[Inexact] = False
            ctx.prec *= 2
            result = ctx.divide(numerator, denominator)

        return result


class CNABExporter(osv.osv_memory):
    _name = 'cnab.wizard.exporter'

    def _round(self, v):
        v = float_to_decimal(v)
        return (v * Decimal('100')).quantize(1)

    def _only_digits(self, v):
        if not v:
            return v == ''
        else:
            return re.sub('[^0-9]', '', v)

    def _spe_char_remove(self, text):
        if not text:
            return text == ''
        else:
            text = text.encode('utf-8')
            dic = {
                '\xc3\xa1': 'a',
                '\xc3\xa0': 'a',
                '\xc3\xa2': 'a',
                '\xc3\xa3': 'a',
                '\xc3\x81': 'A',
                '\xc3\x80': 'A',
                '\xc3\x82': 'A',
                '\xc3\x83': 'A',
                '\xc3\xa9': 'e',
                '\xc3\xa8': 'e',
                '\xc3\xaa': 'e',
                '\xe1\xba\xbd': 'e',
                '\xc3\x89': 'E',
                '\xc3\x88': 'E',
                '\xc3\x8a': 'E',
                '\xe1\xba\xbc': 'E',
                '\xc3\xad': 'i',
                '\xc3\xac': 'i',
                '\xc3\xae': 'i',
                '\xc4\xa9': 'i',
                '\xc3\x8d': 'I',
                '\xc3\x8c': 'I',
                '\xc3\x8e': 'I',
                '\xc4\xa8': 'I',
                '\xc3\xb3': 'o',
                '\xc3\xb2': 'o',
                '\xc3\xb4': 'o',
                '\xc3\xb5': 'o',
                '\xc3\x93': 'O',
                '\xc3\x92': 'O',
                '\xc3\x94': 'O',
                '\xc3\x95': 'O',
                '\xc3\xba': 'u',
                '\xc3\xb9': 'u',
                '\xc3\xbb': 'u',
                '\xc5\xa9': 'u',
                '\xc3\x9a': 'U',
                '\xc3\x99': 'U',
                '\xc3\x9b': 'U',
                '\xc5\xa8': 'U',
                '\xc3\xa7': 'c',
                '\xc3\x87': 'C'
            }
            for s, r in dic.iteritems():
                text = text.replace(s, r)

            return re.sub('[^a-zA-Z0-9/&. -]', '', text)

    def _get_address(self, partner, len_adress):
        if partner.street2:
            w_address = '%s, %s, %s ' % (
                partner.street or '', partner.number or '',
                partner.street2 or '')
        else:
            w_address = '%s, %s' % (partner.street or '', partner.number or '')
        if len(w_address) > len_adress:
            difference = len(w_address) - len_adress
            w_street = partner.street
            w_street = w_street.encode('latin-1')
            w_street = w_street[:len(w_street) - difference]
            w_street = w_street.decode('unicode-escape')
            if partner.street2:
                w_address = '%s, %s, %s ' % (
                    w_street or '', partner.number or '', partner.street2)
            else:
                w_address = '%s, %s' % (w_street or '', partner.number or '')
        return self._spe_char_remove(w_address)

    def header(self, cr, uid, rec_payment_type):
        return {
            'IDReg': '0',
            'AgenciaCedente': rec_payment_type.bank_account.bra_number,
            'ContaCorrente': rec_payment_type.bank_account.acc_number,
            'DigitoContaCorrente': rec_payment_type.bank_account.acc_number_dig,
            'NomeEmpresa': self._spe_char_remove(
                rec_payment_type.company_id.legal_name),
            'DataGravacaoArquivo': date.today(),
            'Mensagem1': '',
            'Mensagem2': '',
            'Mensagem3': '',
            'Mensagem4': '',
            'Mensagem5': '',
            'Mensagem6': ''
        }

    def detalhe(self, cr, uid, rec_account_move_line):
        interest = rec_account_move_line.payment_type.bank_account.monthly_interest
        perc_monthly_fine = rec_account_move_line.payment_type.bank_account.monthly_fine
        perc_monthly_fine = str(perc_monthly_fine)
        if rec_account_move_line.company_id.partner_id.is_company:
            company_cnpj_cpf = '02'
        else:
            company_cnpj_cpf = '01'
        if rec_account_move_line.partner_id.is_company:
            partner_cnpj_cpf = '02'
        else:
            partner_cnpj_cpf = '01'
        monthly_fine = rec_account_move_line.debit / 100
        monthly_fine = monthly_fine * interest
        monthly_fine = round(monthly_fine, 5)
        monthly_fine = str(monthly_fine)
        return {
            'IDReg': '1',
            'IdentificacaoInscricaoCedente': company_cnpj_cpf,
            'NInscricaoEmpresa': self._only_digits(rec_account_move_line.company_id.cnpj_cpf),
            'AgenciaCedente': rec_account_move_line.payment_type.bank_account.bra_number,
            'DigitoAgenciaCedente': rec_account_move_line.payment_type.bank_account.bra_number_dig,
            'ContaCorrente': rec_account_move_line.payment_type.bank_account.acc_number,
            'DigitoContaCedente': rec_account_move_line.payment_type.bank_account.acc_number_dig,
            'ConvenioCobranca': rec_account_move_line.payment_type.bank_account.bank_col_agreement,
            'UsoEmpresa': '',
            'NossoNumero': rec_account_move_line.our_number,
            'Carteira': rec_account_move_line.payment_type.bank_account.bank_col_service,
            'UsoBanco': '',
            'NDocumento': rec_account_move_line.name,
            'DataVencimentoTitulo': datetime.strptime(rec_account_move_line.date_maturity, '%Y-%m-%d'),
            'ValorTitulo': self._round(rec_account_move_line.debit),
            'DataEmissaoTitulo': datetime.strptime(rec_account_move_line.date, '%Y-%m-%d'),
            '1Instrucao': '',
            '2Instrucao': '',
            'MoraDiaria': self._only_digits(monthly_fine),
            'DataLimiteDesconto': '',
            'ValorDesconto': 0,
            'ValorIOF': 0,
            'ValorAbatimento': 0,
            'IdentificacaoInscricaoSacado': partner_cnpj_cpf,
            'NInscricaoSacado': self._only_digits(
                rec_account_move_line.partner_id.cnpj_cpf),
            'NomeSacado': self._spe_char_remove(
                rec_account_move_line.partner_id.legal_name),
            'EnderecoCompleto40': self._get_address(
                rec_account_move_line.partner_id, 40),
            'Bairro': self._spe_char_remove(
                rec_account_move_line.partner_id.district),
            'Cep': self._only_digits(rec_account_move_line.partner_id.zip),
            'Cidade': self._spe_char_remove(
                rec_account_move_line.partner_id.l10n_br_city_id.name),
            'Estado': rec_account_move_line.partner_id.state_id and rec_account_move_line.partner_id.state_id.code or '',
            'SacadorAvalista': '',
            'DataMora': '',
            'Prazo': '',
            'PercentualMulta': self._only_digits(perc_monthly_fine),
            'ComplementoConta': '',
            'DiasProtesto': ''
        }

    def trailer(self, cont_title_banks):
        return {
            'IDReg': '9',
            'QuantidadeTitulos': cont_title_banks,
            'ValorTotal': ''
        }

    def generate_remessa(self, cr, uid, ids, context=None):
        obj_account_move_line = self.pool.get('account.move.line')
        br_account_move_line = obj_account_move_line.browse(
            cr, uid, context['active_ids'], context=context)
        obj_bank_file = self.pool.get('account.bank.file')
        br_bank_file = obj_bank_file.browse(
            cr, uid, context['active_ids'], context=context)
        for rec_bank_file in br_bank_file:
            w_id = rec_bank_file.id

        obj_payment_type = self.pool.get('payment.type')
        src_payment_type = obj_payment_type.search(
            cr, uid, [('layout_remessa', '!=', False)])
        br_payment_type = obj_payment_type.browse(
            cr, uid, src_payment_type, context=context)
        cont_title_banks = 0
        for rec_payment_type in br_payment_type:
            file_remessa = []
            for rec_account_move_line in br_account_move_line:
                if rec_account_move_line.payment_type.code == rec_payment_type.code:
                    if file_remessa == []:
                        file_remessa.append(
                            self.header(cr, uid, rec_payment_type))
                    file_remessa.append(
                        self.detalhe(cr, uid, rec_account_move_line))
                    cont_title_banks = cont_title_banks + 1

            if file_remessa != []:
                file_remessa.append(self.trailer(cont_title_banks))
                for i, line in zip(counter(start=1), file_remessa):
                    line['NroSequencialRegistro'] = i

            w_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
            now = datetime.now(pytz.timezone(w_timezone))
            now_utc = datetime.today()
            if rec_payment_type.layout_remessa.filename:
                filename = rec_payment_type.layout_remessa.filename
            else:
                filename = 'REM_%s_%04d%02d%02d_%02d%02d%02d.txt' % (
                    rec_payment_type.bank_account.bank.bic,
                    now.year, now.month, now.day, now.hour, now.minute,
                    now.second)
            result = self.serialize(
                cr, uid, rec_payment_type.layout_remessa, file_remessa)
            encoded_result = base64.b64encode(result)
            obj_bank_file.create(cr, uid, {
                'cnab_file': encoded_result,
                'filename': filename,
                'file_type': 'remessa',
                'date_time': now_utc,
                'bank': rec_payment_type.bank_account.bank.id
                }
            )
            if context.get('open_bank_file', False):
                return self.open_bank_file(cr, uid, ids, context=context)
            return {'type': 'ir.actions.act_window_close'}

    def open_bank_file(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        tree_res = ir_model_data.get_object_reference(
            cr, uid, 'bank_transaction', 'bank_file_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Consult Bank File'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.bank.file',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'type': 'ir.actions.act_window'
        }

    def serialize(self, cr, uid, format, data):
        generator = CNABGenerator()
        result = generator.generate_file(format, data).read()
        return result


CNABExporter()
