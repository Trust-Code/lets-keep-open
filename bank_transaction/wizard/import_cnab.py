# Embedded file name: /opt/openerp/producao/addons-extra/bank_transaction/wizard/import_cnab.py
import netsvc
from tools.translate import _
from osv import osv, fields
import pytz
from datetime import datetime, date
from cStringIO import StringIO
from decimal import Decimal
import logging
import base64
from parser import CNABParser


class CNABImporter(osv.osv_memory):
    _name = 'cnab.wizard.importer'

    def generate_payment_with_journal(
        self, cr, uid, journal_id, bank_account_id,
        partner_id, amount_payment_slip, amount, entry_name,
        date, should_validate, context):
        """
        Generate a voucher for the payment

        It will try to match with the invoice of the order by
        matching the payment ref and the invoice origin.

        The invoice does not necessarily exists at this point, so if yes,
        it will be matched in the voucher, otherwise, the voucher won't
        have any invoice lines and the payment lines will be reconciled
        later with "auto-reconcile" if the option is used.

        """
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')
        journal = self.pool.get('account.journal').browse(
            cr, uid, journal_id, context=context)
        w_period_ids = self.pool.get('account.period').find(
            cr, uid, context=context)
        voucher_vals = {
            'reference': entry_name,
            'journal_id': journal.id,
            'amount': amount,
            'period_id': w_period_ids and w_period_ids[0] or False,
            'date': date,
            'partner_id': partner_id,
            'account_id': journal.default_credit_account_id.id,
            'currency_id': journal.company_id.currency_id.id,
            'company_id': journal.company_id.id,
            'type': 'receipt',
            'comment': entry_name
        }
        if voucher_vals['amount'] > amount_payment_slip:
            br_res_partner_bank = self.pool.get('res.partner.bank').browse(
                cr, uid, bank_account_id)
            voucher_vals.update({
                'payment_option': br_res_partner_bank.payment_option_default,
                'writeoff_acc_id': br_res_partner_bank.writeoff_acc_id_default.id
            })
        voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=context)
        onchange_voucher = voucher_obj.onchange_partner_id(
            cr, uid, [], partner_id=partner_id, journal_id=journal.id,
            amount=amount, currency_id=journal.company_id.currency_id.id,
            ttype='receipt', date=date, context=context)['value']
        matching_line = {}
        if onchange_voucher.get('line_cr_ids'):
            voucher_lines = onchange_voucher['line_cr_ids']
            line_ids = [line['move_line_id'] for line in voucher_lines]
            matching_ids = [line.id for line in move_line_obj.browse(
                cr, uid, line_ids, context=context) if line.ref == entry_name]
            matching_lines = [line for line in voucher_lines if line['move_line_id'] in matching_ids]
            if matching_lines:
                matching_line = matching_lines[0]
                if voucher_vals['amount'] > amount_payment_slip:
                    amount = voucher_vals['amount'] - amount_payment_slip
                    amount = voucher_vals['amount'] - amount
                matching_line.update({
                    'amount': amount,
                    'voucher_id': voucher_id
                })
                amount_pay = matching_line['amount']
                src_voucher_line = voucher_line_obj.search(
                    cr, uid, [('voucher_id', '=', voucher_id),
                              ('reconcile', '=', True)])
                if src_voucher_line:
                    amount_voucher_lines = 0
                    for rec_voucher_line in src_voucher_line:
                        _w_amount = voucher_line_obj.browse(
                            cr, uid, rec_voucher_line).amount
                        amount_voucher_lines = amount_voucher_lines + _w_amount
                        amount_pay = amount_voucher_lines + amount_pay

                if amount_pay == amount_payment_slip:
                    matching_line.update({'reconcile': True})
        if matching_line:
            voucher_line_obj.create(cr, uid, matching_line, context=context)
        if should_validate:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(
                uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        return voucher_id

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

    def open_bank_statement(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(
            cr, uid, 'account', 'view_bank_statement_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(
            cr, uid, 'account', 'view_bank_statement_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Consult Bank Statement'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'account.bank.statement',
            'view_id': False,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window'
        }

    def _pay_invoice(self, cr, uid, journal, bank_account_id,
                     rec_account_move_line, payment_date, payment_amount):
        period_obj = self.pool.get('account.period')
        company_id = self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.voucher')
        period_id, = period_obj.find(
            cr, uid, payment_date, {'company_id': company_id})
        account_id = rec_account_move_line.partner_id.property_account_receivable.id
        self.generate_payment_with_journal(
            cr, uid, journal.id, bank_account_id,
            rec_account_move_line.partner_id.id, rec_account_move_line.debit,
            payment_amount, rec_account_move_line.move_id.ref, payment_date,
            True, context={'invoice_id': rec_account_move_line.id})

    def _cents_to_euros(self, value):
        return float((Decimal(value) / Decimal('100')).quantize(Decimal('1.00')))

    def import_file(self, cr, uid, ids, context=None):
        obj_account_move_line = self.pool.get('account.move.line')
        obj_bank_file = self.pool.get('account.bank.file')
        wizard, = self.browse(cr, uid, ids)
        data = base64.b64decode(wizard.file)
        cnab_file = StringIO(data)
        parser = CNABParser()
        if wizard.type == 'retorno':
            format = wizard.payment_type.layout_retorno
            try:
                payments = [line for line in parser.parse_file(format, cnab_file) if line['IDReg'] == '1']
            except:
                raise osv.except_osv('Error', 'Invalid File')

            journal = wizard.payment_type.bank_account.journal_id
            if not journal:
                raise osv.except_osv('Error', 'Please configure bank journal')
            not_found = []
            for line in payments:
                if obj_account_move_line.search(
                   cr, uid, [('name', '=', line['NDocumento'])]):
                    src_account_move_line = obj_account_move_line.search(
                        cr, uid, [('name', '=', line['NDocumento'])])
                    rec_account_move_line = obj_account_move_line.browse(
                        cr, uid, src_account_move_line[0])
                    for events in wizard.payment_type.bank_account.bank.code_occurrence_ids:
                        if events.code_occurrence == line['IdentificacaoOcorrencia']:
                            if events.action == 'pay':
                                try:
                                    value = self._cents_to_euros(line['ValorPrincipal'])
                                    payment_date = line['DataOcorrencia'].isoformat()
                                    self._pay_invoice(cr, uid, journal, wizard.payment_type.bank_account.id, rec_account_move_line, payment_date, value)
                                except ValueError:
                                    not_found.append(str(line['IdentificacaoTitulo1']))

                                logging.error("Couldn't find the following invoices: %s", ', '.join(not_found))
                            elif events.action == 'confirm':
                                obj_account_move_line.write(
                                    cr, uid, rec_account_move_line.id,
                                    {'status_aux': 'confirm',
                                     'our_number': line['NossoNumero']})

            w_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
            now = datetime.now(pytz.timezone(w_timezone))
            now_utc = datetime.today()
            if wizard.payment_type.layout_retorno.filename:
                filename = wizard.payment_type.layout_retorno.filename
            else:
                filename = 'RET_%s_%04d%02d%02d_%02d%02d%02d.txt' % (
                    wizard.payment_type.bank_account.bank.bic,
                    now.year, now.month, now.day, now.hour,
                    now.minute, now.second)
            obj_bank_file.create(cr, uid, {
                'cnab_file': wizard.file,
                'filename': filename,
                'file_type': 'retorno',
                'date_time': now_utc,
                'bank': wizard.payment_type.bank_account.bank.id
                })
            return self.open_bank_file(cr, uid, ids, context=context)
        if wizard.type == 'extrato':
            format = wizard.payment_type.layout_extrato
        try:
            payments = [line for line in parser.parse_file(format, cnab_file) if line['IDReg'] == '3']
        except:
            raise osv.except_osv('Error', 'Invalid File')

        obj_account_bank_statement = self.pool.get('account.bank.statement')
        obj_account_bank_statement_line = self.pool.get('account.bank.statement.line')
        obj_account_period = self.pool.get('account.period')
        journal = wizard.payment_type.bank_account.journal_id
        memory_date = False
        for line in payments:
            if line['DataLancamento'] != memory_date:
                _w_date = datetime.strptime(
                    line['DataLancamento'], '%d%m%Y').date()
                period = '%s/%s' % (_w_date.strftime('%m'), _w_date.strftime('%Y'))
                scr_account_period = obj_account_period.search(
                    cr, uid, [('name', '=', period)])
                reference = '%s - %s' % (journal.name, _w_date)
                vals = {
                    'name': reference,
                    'date': _w_date,
                    'journal_id': journal.id,
                    'period_id': scr_account_period[0]}
                obj_account_bank_statement.create(
                    cr, uid, vals, context=context)
                memory_date = line['DataLancamento']
            if line['DataLancamento'] == memory_date:
                date_release = datetime.strptime(
                    line['DataLancamento'], '%d%m%Y').date()
                name_item = line['Historico']
                amount = self._cents_to_euros(line['ValorLancamento'])
                scr_account_bank_statement = obj_account_bank_statement.search(
                    cr, uid, [('name', '=', reference)])
                if line['TipoLancamento'] == 'D':
                    if wizard.payment_type.company_id.partner_default_account_payable_id.id:
                        account_id = wizard.payment_type.company_id.partner_default_account_payable_id.id
                    else:
                        raise osv.except_osv(
                            'Error', 'Not Found "Account Payment Default"')
                elif line['TipoLancamento'] == 'C':
                    if wizard.payment_type.company_id.partner_default_account_receivable_id.id:
                        account_id = wizard.payment_type.company_id.partner_default_account_receivable_id.id
                    else:
                        raise osv.except_osv(
                            'Error', 'Not Found "Account Receive Default"')
                items = {
                    'date': date_release,
                    'name': name_item,
                    'amount': amount,
                    'statement_id': scr_account_bank_statement[0],
                    'account_id': account_id
                }
                obj_account_bank_statement_line.create(
                    cr, uid, items, context=context)

        return self.open_bank_statement(cr, uid, ids, context=context)

    _columns = {
        'file': fields.binary('File', required=True),
        'type': fields.selection(
            [('retorno', 'Arquivo de Retorno Bancário'),
             ('extrato', 'Arquivo de Extrato Bancário')],
            'File Type', required=True),
        'payment_type': fields.many2one('payment.type', 'Payment Type')
    }
