# Embedded file name: /opt/openerp/producao/addons-extra/bank_transaction/payment_slip.py
from datetime import datetime, date
from osv import osv, fields
from openerp.osv import osv, fields
from pyboleto.pdf import BoletoPDF
from pyboleto.bank.itau import BoletoItau
from pyboleto.bank.santander import BoletoSantander
from tools.translate import _
import tempfile
import base64
from openerp.osv import fields, orm


class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    def status_default(self, cr, uid, ids, field_names, args, context=None):
        w_status = dict.fromkeys(ids, False)
        for line in self.browse(cr, uid, ids, context=context):
            if line.reconcile_id:
                w_status[line.id] = 'Pago'
            elif line.status_aux:
                w_status[line.id] = 'Confirmado'
            else:
                w_status[line.id] = 'Aberto'

        return w_status

    def get_file(self, cr, uid, ids, field_names, args, context=None):
        if not ids:
            return []
        else:
            obj_ir_attachment = self.pool.get('ir.attachment')
            res = {}
            for record in self.read(cr, uid, ids, ['res_id'], context=context):
                res[record['id']] = False
                src_ir_attachment = obj_ir_attachment.search(
                    cr, uid, [('res_model', '=', 'account.move.line'),
                              ('res_id', '=', record['id'])])
                if src_ir_attachment:
                    file_data = obj_ir_attachment._data_get(
                        cr, uid, src_ir_attachment, field_names, args,
                        context=None)
                    if file_data:
                        res[record['id']] = file_data[src_ir_attachment[0]]

            return res

    _columns = {
        'status': fields.function(status_default, type='char',
                                  string='Status'),
        'status_aux': fields.char('Status Auxiliary', size=128),
        'slip_file': fields.function(get_file, type='binary',
                                     string='Slip File'),
        'filename': fields.char('Filename', size=128),
        'slip_create_date': fields.date('Slip Create Date'),
        'our_number': fields.text('Our Number', size=128)
    }
    _defaults = {}


class res_partner_bank(osv.osv):
    _name = 'res.partner.bank'
    _inherit = 'res.partner.bank'
    _columns = {
        'bank_col_service': fields.char('Bank Collection Service', size=3),
        'bank_col_agreement': fields.char('Bank Collection Agreement', size=7),
        'monthly_fine': fields.float('Monthly Fine for Delay (%)', size=5),
        'monthly_interest': fields.float('Monthly Interest (%)', size=5),
        'instructions': fields.text('Instructions'),
        'generate_payment_slip': fields.boolean('Payment Slip Generate'),
        'payment_option_default': fields.selection(
            [('without_writeoff', 'Keep Open'),
             ('with_writeoff', 'Reconcile Payment Balance')],
            'Payment Difference Default'),
        'writeoff_acc_id_default': fields.many2one(
            'account.account', 'Counterpart Account Default')
    }
    _defaults = {}


class payment_slip(osv.osv):
    _name = 'payment.slip'

    def slip(self, cr, uid, ids, context=None):
        obj_account_move_line = self.pool.get('account.move.line')
        br_account_move_line = obj_account_move_line.browse(
            cr, uid, context['active_ids'], context=context)
        for rec_account_move_line in br_account_move_line:
            bank_cod = rec_account_move_line.payment_type.bank_account.bank.bic
            if bank_cod == '341':
                self.gerar_boleto_itau(
                    cr, uid, rec_account_move_line, context=None)
            elif bank_cod == '033':
                self.gerar_boleto_santander(
                    cr, uid, rec_account_move_line, context=None)

        return

    def gerar_boleto_itau(self, cr, uid, rec_account_move_line, context=None):
        obj_ir_attachment = self.pool.get('ir.attachment')
        obj_account_move_line = self.pool.get('account.move.line')
        if rec_account_move_line.payment_type.type_banking_billing == 'REG' or \
           rec_account_move_line.payment_type.type_banking_billing == 'SRG':
            our_number = self.pool.get('ir.sequence').get(
                cr, uid, 'payment_slip_our_number_itau')
            obj_account_move_line.write(
                cr, uid, rec_account_move_line.id, {'our_number': our_number},
                context=context)
        if not rec_account_move_line.our_number:
            raise osv.except_osv(
                _('Error'),
                _('Error! Confirmation file has not validated by the bank!'))
        instruct = rec_account_move_line.payment_type.bank_account.instructions
        if instruct:
            fine = rec_account_move_line.payment_type.bank_account.monthly_fine
            interest = rec_account_move_line.payment_type.bank_account.monthly_interest
            value_fine = rec_account_move_line.debit / 100
            value_fine = value_fine * fine
            value_fine = round(value_fine, 2)
            value_fine = str(value_fine)
            value_interest = rec_account_move_line.debit / 100
            value_interest = value_interest * interest
            value_interest = round(value_interest, 2)
            value_interest = str(value_interest)
            instruct = instruct.replace('%(monthly_fine)s', value_fine)
            instruct = instruct.replace('%(monthly_interest)s', value_interest)
        if rec_account_move_line.partner_id.street2:
            sacado_endereco_1 = '%s, %s - %s - %s' % (
                rec_account_move_line.partner_id.street,
                rec_account_move_line.partner_id.number,
                rec_account_move_line.partner_id.street2,
                rec_account_move_line.partner_id.district)
        else:
            sacado_endereco_1 = '%s, %s - %s' % (
                rec_account_move_line.partner_id.street,
                rec_account_move_line.partner_id.number,
                rec_account_move_line.partner_id.district)
        sacado_endereco_2 = '%s - %s/%s' % (
            rec_account_move_line.partner_id.zip,
            rec_account_move_line.partner_id.city,
            rec_account_move_line.partner_id.state_id.code)
        cedente_endereco = '%s, %s - %s - %s/%s' % (
            rec_account_move_line.company_id.street,
            rec_account_move_line.company_id.number,
            rec_account_move_line.company_id.zip,
            rec_account_move_line.company_id.city,
            rec_account_move_line.company_id.state_id.code)
        cedente = rec_account_move_line.company_id.legal_name
        if len(cedente) > 40:
            difference = len(cedente) - 40
            cedente = cedente[:len(cedente) - difference]
        sacado_nome = rec_account_move_line.partner_id.legal_name
        if len(sacado_nome) > 40:
            difference = len(sacado_nome) - 40
            sacado_nome = sacado_nome[:len(sacado_nome) - difference]
        error = []
        if not rec_account_move_line.company_id.partner_id.cnpj_cpf:
            error.append('CPF/CNPJ (cedente)')
        if not rec_account_move_line.payment_type.bank_account.bank_col_service:
            error.append('Carteira Bancaria')
        if error:
            raise orm.except_orm(
                _('Error'),
                _('Missing data for generating the payment slip:\n%s') % error)
        lista_dados_itau = []
        obj_boleto = BoletoItau()
        obj_boleto.cedente = cedente
        obj_boleto.cedente_documento = rec_account_move_line.company_id.partner_id.cnpj_cpf
        obj_boleto.cedente_endereco = cedente_endereco
        obj_boleto.agencia_cedente = rec_account_move_line.payment_type.bank_account.bra_number
        obj_boleto.conta_cedente = rec_account_move_line.payment_type.bank_account.acc_number
        obj_boleto.data_vencimento = datetime.date(datetime.strptime(rec_account_move_line.date_maturity, '%Y-%m-%d'))
        obj_boleto.data_processamento = date.today()
        obj_boleto.data_documento = datetime.date(datetime.strptime(rec_account_move_line.date, '%Y-%m-%d'))
        obj_boleto.instrucoes = instruct or ''
        obj_boleto.valor_documento = rec_account_move_line.debit
        obj_boleto.nosso_numero = rec_account_move_line.our_number
        obj_boleto.numero_documento = rec_account_move_line.name
        obj_boleto.tipo_boleto = '1'
        obj_boleto.carteira = rec_account_move_line.payment_type.bank_account.bank_col_service
        obj_boleto.demonstrativo = ''
        obj_boleto.sacado = ['%s' % sacado_nome, '%s' % sacado_endereco_1, '%s' % sacado_endereco_2]
        lista_dados_itau.append(obj_boleto)
        if obj_boleto.tipo_boleto == '1':
            w_file = tempfile.NamedTemporaryFile(
                prefix='Slip', suffix='.pdf', delete=False)
            w_slip = BoletoPDF(w_file)
            for i in range(len(lista_dados_itau)):
                w_slip.drawBoleto(lista_dados_itau[i])
                w_slip.nextPage()

            w_slip.save()
            due_date = datetime.date(datetime.strptime(
                rec_account_move_line.date_maturity, '%Y-%m-%d'))
            filename = 'BOL_%s_%04d%02d%02d.pdf' % (
                rec_account_move_line.partner_id.name,
                due_date.year, due_date.month, due_date.day)
            w_file.seek(0)
            fl = w_file.read()
            src_ir_attachment = obj_ir_attachment.search(
                cr, uid, [('res_id', '=', rec_account_move_line.id)])
            if src_ir_attachment:
                attach_val = {
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(fl)
                }
                obj_ir_attachment.write(
                    cr, uid, src_ir_attachment, attach_val, context=context)
            else:
                attach_vals = {
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(fl),
                    'file_type': format,
                    'res_model': 'account.move.line',
                    'res_id': rec_account_move_line.id
                }
                obj_ir_attachment.create(cr, uid, attach_vals, context=context)
                pay_slip_vals = {
                    'filename': filename,
                    'slip_create_date': date.today()
                }
                obj_account_move_line.write(
                    cr, uid, rec_account_move_line.id, pay_slip_vals,
                    context=context)
                w_file.close()

    def gerar_boleto_santander(self, cr, uid, rec_account_move_line,
                               context=None):
        obj_ir_attachment = self.pool.get('ir.attachment')
        obj_account_move_line = self.pool.get('account.move.line')
        if rec_account_move_line.payment_type.type_banking_billing == 'REG' or rec_account_move_line.payment_type.type_banking_billing == 'SRG':
            our_number = self.pool.get('ir.sequence').get(
                cr, uid, 'payment_slip_our_number_itau')
            obj_account_move_line.write(
                cr, uid, rec_account_move_line.id, {'our_number': our_number},
                context=context)
        if not rec_account_move_line.our_number:
            raise osv.except_osv(
                _('Error'),
                _('Error! Payment slip does not yet confirmed by the bank.'))
        instruct = rec_account_move_line.payment_type.bank_account.instructions
        if instruct:
            fine = rec_account_move_line.payment_type.bank_account.monthly_fine
            interest = rec_account_move_line.payment_type.bank_account.monthly_interest
            value_fine = rec_account_move_line.debit / 100
            value_fine = value_fine * fine
            value_fine = round(value_fine, 2)
            value_fine = str(value_fine)
            value_interest = rec_account_move_line.debit / 100
            value_interest = value_interest * interest
            value_interest = round(value_interest, 2)
            value_interest = str(value_interest)
            instruct = instruct.replace('%(monthly_fine)s', value_fine)
            instruct = instruct.replace('%(monthly_interest)s', value_interest)
        if rec_account_move_line.partner_id.street2:
            sacado_endereco_1 = '%s, %s - %s - %s' % (
                rec_account_move_line.partner_id.street,
                rec_account_move_line.partner_id.number,
                rec_account_move_line.partner_id.street2,
                rec_account_move_line.partner_id.district)
        else:
            sacado_endereco_1 = '%s, %s - %s' % (
                rec_account_move_line.partner_id.street,
                rec_account_move_line.partner_id.number,
                rec_account_move_line.partner_id.district)
        sacado_endereco_2 = '%s - %s/%s' % (
            rec_account_move_line.partner_id.zip,
            rec_account_move_line.partner_id.city,
            rec_account_move_line.partner_id.state_id.code)
        cedente_endereco = '%s, %s - %s - %s/%s' % (
            rec_account_move_line.company_id.street,
            rec_account_move_line.company_id.number,
            rec_account_move_line.company_id.zip,
            rec_account_move_line.company_id.city,
            rec_account_move_line.company_id.state_id.code)
        sacado_nome = rec_account_move_line.partner_id.legal_name
        error = []
        if not rec_account_move_line.company_id.partner_id.cnpj_cpf:
            error.append('CPF/CNPJ (cedente)')
        if not rec_account_move_line.payment_type.bank_account.bank_col_service:
            error.append('Carteira Bancaria')
        if error:
            raise orm.except_orm(
                _('Error'),
                _('Missing data for generating the payment slip:\n%s') % error)
        lista_dados_santander = []
        obj_boleto = BoletoSantander()
        obj_boleto.cedente = rec_account_move_line.company_id.legal_name
        obj_boleto.cedente_documento = rec_account_move_line.company_id.partner_id.cnpj_cpf
        obj_boleto.cedente_endereco = cedente_endereco
        obj_boleto.agencia_cedente = rec_account_move_line.payment_type.bank_account.bra_number
        obj_boleto.conta_cedente = rec_account_move_line.payment_type.bank_account.acc_number
        obj_boleto.data_vencimento = datetime.date(datetime.strptime(rec_account_move_line.date_maturity, '%Y-%m-%d'))
        obj_boleto.data_processamento = date.today()
        obj_boleto.data_documento = datetime.date(datetime.strptime(rec_account_move_line.date, '%Y-%m-%d'))
        obj_boleto.instrucoes = instruct or ''
        obj_boleto.valor_documento = rec_account_move_line.debit
        obj_boleto.nosso_numero = rec_account_move_line.our_number
        obj_boleto.numero_documento = rec_account_move_line.name
        obj_boleto.tipo_boleto = '1'
        obj_boleto.carteira = rec_account_move_line.payment_type.bank_account.bank_col_service
        obj_boleto.demonstrativo = ''
        obj_boleto.sacado = ['%s' % sacado_nome, '%s' % sacado_endereco_1, '%s' % sacado_endereco_2]
        lista_dados_santander.append(obj_boleto)
        if obj_boleto.tipo_boleto == '1':
            w_file = tempfile.NamedTemporaryFile(
                prefix='Slip', suffix='.pdf', delete=False)
            w_slip = BoletoPDF(w_file)
            for i in range(len(lista_dados_santander)):
                w_slip.drawBoleto(lista_dados_santander[i])
                w_slip.nextPage()

            w_slip.save()
            due_date = datetime.date(datetime.strptime(rec_account_move_line.date_maturity, '%Y-%m-%d'))
            filename = 'BOL_%s_%04d%02d%02d.pdf' % (
                rec_account_move_line.partner_id.name,
                due_date.year,
                due_date.month,
                due_date.day)
            w_file.seek(0)
            fl = w_file.read()
            src_ir_attachment = obj_ir_attachment.search(
                cr, uid, [('res_id', '=', rec_account_move_line.id)])
            if src_ir_attachment:
                attach_val = {
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(fl)
                }
                obj_ir_attachment.write(cr, uid, src_ir_attachment,
                                        attach_val, context=context)
            else:
                attach_vals = {
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(fl),
                    'file_type': format,
                    'res_model': 'account.move.line',
                    'res_id': rec_account_move_line.id
                }
                obj_ir_attachment.create(cr, uid, attach_vals, context=context)
                pay_slip_vals = {
                    'filename': filename,
                    'slip_create_date': date.today()
                }
                obj_account_move_line.write(
                    cr, uid, rec_account_move_line.id, pay_slip_vals,
                    context=context)
                w_file.close()

    def send_email(self, cr, uid, ids, context=None):
        obj_ir_attachment = self.pool.get('ir.attachment')
        obj_account_move_line = self.pool.get('account.move.line')
        br_account_move_line = obj_account_move_line.browse(
            cr, uid, context['active_ids'], context=context)
        for rec_account_move_line in br_account_move_line:
            attachment_ids = obj_ir_attachment.search(
                cr, uid, [('res_model', '=', 'account.move.line'),
                          ('res_id', '=', rec_account_move_line.id)])
            obj_email_template = self.pool.get('email.template')
            template_id = obj_email_template.search(
                cr, uid, [('model', '=', 'account.move.line')])
            mail_values = obj_email_template.generate_email(
                cr, uid, template_id[0], rec_account_move_line.id,
                context=context)
            email = rec_account_move_line.partner_id.email and rec_account_move_line.partner_id.email or ''
            obj_res_partner = self.pool.get('res.partner')
            src_res_partner_child = obj_res_partner.search(
                cr, uid, [('is_company', '=', False),
                          ('parent_id', '=', rec_account_move_line.partner_id.id),
                          ('send_payment_slip', '=', True)])
            email_child = ''
            if src_res_partner_child:
                partners = obj_res_partner.browse(cr, uid, src_res_partner_child)
                for rec_res_partner_child in partners:
                    email_child += rec_res_partner_child.email and \
                        rec_res_partner_child.email + '; ' or ''

            vals = {
                'subject': mail_values['subject'],
                'email_from': mail_values['email_from'],
                'email_to': email,
                'email_cc': email_child,
                'body_html': mail_values['body_html'],
                'auto_delete': True,
                'state': 'outgoing',
                'model': mail_values['model'],
                'res_id': mail_values['res_id'],
                'attachment_ids': [(6, 0, attachment_ids)]
            }
            self.pool.get('mail.mail').create(cr, uid, vals, context=context)
