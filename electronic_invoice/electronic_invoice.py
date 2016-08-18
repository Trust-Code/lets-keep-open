# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import random
import os
import base64
import urllib2
import datetime
import requests
import xml.etree.ElementTree as ET
from openerp.osv import fields, osv
from openerp.tools.translate import _
from uuid import uuid4

class electronic_invoice(osv.osv):
    _name = 'electronic.invoice'

    def create_temp_file(self, content_file, path = None):
        if not path:
            path = '/tmp'
        if not os.path.exists(path):
            os.makedirs(path)
        name = uuid4().hex
        w_file = open(path + '/' + name, 'w')
        w_file.write(content_file)
        w_file.close()
        return name

    def inv_write(self, cr, uid, ids, inv, args, context = None):
        attachment_obj = self.pool.get('ir.attachment')
        self.pool.get('electronic.invoice.event').create(cr, uid, {'invoice_id': inv.id,
         'action': False if 'action' not in args else args['action'],
         'message': False if 'message' not in args else args['message']}, context=context)
        args_inv = args
        del args_inv['message']
        del args_inv['action']
        if args_inv:
            self.pool.get('account.invoice').write(cr, uid, [inv.id], args_inv)
        if 'xml_send' in args:
            attachment_obj.create(cr, uid, {'name': 'nfe-{0}-{1}.xml'.format(inv.internal_number.zfill(10), '{:%Y%m%d}'.format(datetime.datetime.now())),
             'datas': base64.b64encode(args['xml_send'].encode('utf-8')),
             'datas_fname': '.xml',
             'description': '' or _('No Description'),
             'res_model': 'account.invoice',
             'res_id': inv.id,
             'type': 'binary'}, context=context)
        if 'ei_image' in args:
            attachment_obj.create(cr, uid, {'name': 'nfe-{0}-{1}.pdf'.format(inv.internal_number.zfill(10), '{:%Y%m%d}'.format(datetime.datetime.now())),
             'datas': base64.b64encode(args['ei_image']),
             'datas_fname': '.pdf',
             'description': '' or _('No Description'),
             'res_model': 'account.invoice',
             'res_id': inv.id,
             'type': 'binary'}, context=context)
        return True

    def validate_send(self, cr, uid, ids, inv, context=None):
        if not inv.company_id.cnpj_cpf:
            return '%s - %s' % (u'CNPJ do Empresa não informado - ', inv.company_id.name)
        if not inv.company_id.nfe_a1_file:
            return '%s - %s' % (u'Certificado Digital não informado - ', inv.company_id.name)
        if not inv.company_id.nfe_a1_password:
            return '%s - %s' % (u'Senha do Certificado Digital não informada - ', inv.company_id.name)
        if not inv.partner_id.cnpj_cpf:
            return u'CNPJ/CPF do Cliente não informado'
        if not inv.partner_id.state_id:
            return u'UF nao cadastrado para o Cliente informado'
        if not inv.partner_id.state_id.ibge_code:
            return u'Cod. IBGE do UF nao cadastrado para o Cliente informado'
        if not inv.partner_id.l10n_br_city_id:
            return u'Municipio nao cadastrado para o Cliente informado'
        if not inv.partner_id.l10n_br_city_id.ibge_code:
            return u'Cod. IBGE do Municipio nao cadastrado para o Cliente informado'
        if not inv.partner_id.l10n_br_city_id.state_id.id == inv.partner_id.state_id.id:
            return u'UF do municipio diferente da UF do cliente'
        if not inv.document_serie_id:
            return u'Fatura sem Série'
        if not inv.document_serie_id.fiscal_document_id:
            return u'Série sem Documento Fiscal'
        if not inv.document_serie_id.fiscal_document_id.electronic:
            return u'Série não configurada para Nota Fiscal Eletrônica'
        return ''

    def send(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(cr, uid, [('id', 'in', context.get('active_ids'))])
        invoice_br = invoice_obj.browse(cr, uid, invoice_ids, context=context)
        for invoice in invoice_br:
            if invoice.ei_status and invoice.ei_status not in ('failed', 'scheduled'):
                continue
            if invoice.state not in ('open', 'paid'):
                continue
            msg = self.validate_send(cr, uid, ids, invoice, context=context)
            if msg:
                result = {
                    'action': 'send',
                    'status': 'failed',
                    'message': msg}
                self.inv_write(cr, uid, ids, invoice, result, context=context)
                continue
            cert_name = '/tmp/oe_electronic_invoice/' + self.create_temp_file(base64.decodestring(invoice.company_id.nfe_a1_file), path='/tmp/oe_electronic_invoice/')
            if not cert_name:
                result = {
                    'action': 'send',
                    'status': 'failed',
                    'message': 'Digital Certificate can not be saved'}
            elif invoice.fiscal_type == 'product':
                result = self.send_product(cr, uid, ids, invoice, cert_name, context=context)
            elif invoice.company_id.l10n_br_city_id.ibge_code == '50308':
                result = self.send_sp_saopaulo(cr, uid, ids, invoice, cert_name, context=context)
            elif invoice.company_id.l10n_br_city_id.ibge_code in '38709':
                result = self.send_simpliss(cr, uid, ids, invoice, cert_name, context=context)
            elif invoice.company_id.l10n_br_city_id.ibge_code in '44004':
                result = self.send_ariss(cr, uid, ids, invoice, cert_name, context=context)
            else:
                result = {
                    'action': 'send',
                    'status': False,
                    'message': 'Envio de NF-e não disponível'}
            self.inv_write(cr, uid, ids, invoice, result, context=context)
            os.remove(cert_name)

        return True

    def validate_cancel(self, cr, uid, ids, inv, context = None):
        if not inv.company_id.cnpj_cpf:
            return '%s - %s' % (u'CNPJ/CPF da Empresa não informado - ' + inv.company_id.name)
        if not inv.company_id.nfe_a1_file:
            return '%s - %s' % (u'Certificado Digital não informado - ' + inv.company_id.name)
        if not inv.company_id.nfe_a1_password:
            return '%s - %s' % (u'Senha do Certificado Digital não informada - ', inv.company_id.name)
        if not inv.partner_id.cnpj_cpf:
            return '%s' % u'CNPJ/CPF do Cliente não informado'
        return ''

    def cancel(self, cr, uid, ids, context=None):
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_ids = account_invoice_obj.search(cr, uid, [('id', 'in', context.get('active_ids'))])
        account_invoices_br = account_invoice_obj.browse(cr, uid, account_invoice_ids, context=context)
        for invoice in account_invoices_br:
            if not invoice.ei_status:
                continue
            if invoice.ei_status not in 'confirmed':
                continue
            msg = self.validate_cancel(cr, uid, ids, invoice, context=context)
            if msg:
                result = {
                    'action': 'cancel',
                    'message': msg}
                self.inv_write(cr, uid, ids, invoice, result, context=context)
                continue
            cert_name = '/tmp/oe_electronic_invoice/' + self.create_temp_file(base64.decodestring(invoice.company_id.nfe_a1_file), path='/tmp/oe_electronic_invoice/')
            if not cert_name:
                result = {
                    'action': 'cancel',
                    'message': u'Digital Certificate can not be saved'}
            elif invoice.fiscal_type == 'product':
                result = self.cancel_product(cr, uid, ids, invoice, cert_name, context=context)
            elif invoice.company_id.l10n_br_city_id.ibge_code == '50308':
                result = self.cancel_sp_saopaulo(cr, uid, ids, invoice, cert_name, context=context)
            else:
                result = {
                    'action': 'cancel',
                    'message': u'Cancelamento de NF-e nao disponível'}
            self.inv_write(cr, uid, ids, invoice, result, context=context)
            os.remove(cert_name)

        return True

    def validate_inactivate(self, cr, uid, ids, inv, context = None):
        if not inv.company_id.ei_product_version:
            return '%s - %s' % (u'Versão da NF-e não informada -', inv.company_id.name)
        if not inv.company_id.nfe_a1_file:
            return '%s - %s' % (u'Certificado Digital não informado -' + inv.company_id.name)
        if not inv.company_id.nfe_a1_password:
            return '%s - %s' % (u'Senha do Certificado Digital não informada -', inv.company_id.name)
        if not inv.company_id.partner_id or not inv.company_id.partner_id.l10n_br_city_id or not inv.company_id.partner_id.l10n_br_city_id.state_id or not inv.company_id.partner_id.l10n_br_city_id.state_id.code:
            return '%s - %s' % (u'Código do estado no endereço da empresa -', inv.company_id.name)
        if not inv.company_id.cnpj_cpf:
            return '%s - %s' % (u'CNPJ do Empresa não informado - ', inv.company_id.name)
        if not inv.document_serie_id.code:
            return u'Fatura sem Série'
        return ''

    def inactivate(self, cr, uid, ids, context=None, *args):
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_ids = account_invoice_obj.search(cr, uid, [('id', 'in', context.get('active_ids'))])
        account_invoices_br = account_invoice_obj.browse(cr, uid, account_invoice_ids, context=context)
        for invoice in account_invoices_br:
            if invoice.ei_status:
                continue
            if invoice.state not in ('open', 'paid'):
                continue
            msg = self.validate_inactivate(cr, uid, ids, invoice, context=context)
            if msg:
                result = {
                    'action': 'inactivate',
                    'message': msg}
                self.inv_write(cr, uid, ids, invoice, result, context=context)
                continue
            cert_name = '/tmp/oe_electronic_invoice/' + self.create_temp_file(base64.decodestring(invoice.company_id.nfe_a1_file), path='/tmp/oe_electronic_invoice/')
            if not cert_name:
                result = {
                    'action': 'inactivate',
                    'message': u'Digital Certificate can not saved'}
            elif invoice.fiscal_type == 'product':
                result = self.inactivate_product(cr, uid, ids, invoice, cert_name, context=context)
            elif invoice.company_id.l10n_br_city_id.ibge_code == '50308':
                result = self.inactivate_sp_saopaulo(cr, uid, ids, invoice, cert_name, context=context)
            else:
                result = {
                    'action': 'inactivate',
                    'message': u'Inativação de NF-e não disponível'}
            self.inv_write(cr, uid, ids, invoice, result, context=context)
            os.remove(cert_name)

        return True

    def validate_correction_letter(self, cr, uid, ids, inv, context=None):
        if not inv.ei_access_key:
            return '%s' % u'Nota Fiscal sem Chave NF-e'
        if not inv.internal_number:
            return u'Fatura sem número'
        if not inv.ei_correction_letter:
            return '%s' % u'Nota Fiscal sem dados para a Carta de Correção'
        return ''

    def correction_letter(self, cr, uid, ids, context=None, *args):
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_ids = account_invoice_obj.search(
            cr, uid, [('id', 'in', context.get('active_ids'))])
        account_invoices_br = account_invoice_obj.browse(
            cr, uid, account_invoice_ids, context=context)
        for invoice in account_invoices_br:
            if not invoice.ei_status == 'confirmed':
                continue
            if invoice.state not in ('open', 'paid'):
                continue
            if not invoice.fiscal_type == 'product':
                result = {
                    'action': 'correction_letter',
                    'message': u'Carta de Correção não está disponível para a NF-e de serviço.'}
                self.inv_write(cr, uid, ids, invoice, result, context=context)
                continue
            msg = self.validate_correction_letter(cr, uid, ids, invoice, context=context)
            if msg:
                result = {
                    'action': 'correction_letter',
                    'message': msg}
                self.inv_write(cr, uid, ids, invoice, result, context=context)
                continue
            cert_name = '/tmp/oe_electronic_invoice/' + self.create_temp_file(base64.decodestring(invoice.company_id.nfe_a1_file), path='/tmp/oe_electronic_invoice/')
            if not cert_name:
                result = {
                    'action': 'correction_letter',
                    'message': u'Digital Certificate can not be saved'}
            else:
                result = self.correction_letter_product(cr, uid, ids, invoice, cert_name, context=context)
            self.inv_write(cr, uid, ids, invoice, result, context=context)
            os.remove(cert_name)

        return True

    def schedule_to_send(self, cr, uid, ids, context=None):
        obj_account_invoice = self.pool.get('account.invoice')
        src_account_invoice = obj_account_invoice.search(cr, uid, [('id', 'in', context.get('active_ids'))])
        br_account_invoice = obj_account_invoice.browse(cr, uid, src_account_invoice, context=context)
        for rec_account_invoice in br_account_invoice:
            if rec_account_invoice.ei_status and rec_account_invoice.ei_status not in 'failed':
                continue
            if rec_account_invoice.state not in ('open', 'paid'):
                continue
            obj_account_invoice.write(cr, uid, rec_account_invoice.id, {'ei_status': 'scheduled'})

        return True

    def scheduled_sending_invoices(self, cr, uid, context=None):
        if context is None:
            context = {}
        obj_account_invoice = self.pool.get('account.invoice')
        src_account_invoice = obj_account_invoice.search(cr, uid, [('ei_status', '=', 'scheduled')])
        if src_account_invoice:
            if len(src_account_invoice) >= 50:
                src_account_invoice = random.sample(src_account_invoice, 50)
            if 'active_ids' in context:
                context['active_ids'] = src_account_invoice
            else:
                context.update({'active_ids': src_account_invoice})
            self.send(cr, uid, ids=0, context=context)
        else:
            return False
        return True

    def prepare_to_resend(self, cr, uid, ids, context=None):
        for invoice_id in context['active_ids']:
            inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
            if inv.rps_code:
                rps_code = self.pool.get('ir.sequence').get(cr, uid, 'rps.code.seq')
            else:
                raise osv.except_osv(_('Error'), _('Invoice without RPS Number'))
            self.pool.get('account.invoice').write(
                cr, uid, invoice_id, {
                    'rps_code': rps_code,
                    'rps_serie': False,
                    'ei_status': False,
                    'ei_date': False,
                    'ei_code': False,
                    'ei_verification_code': False,
                    'ei_access_key': False,
                    'ei_protocol': False,
                    'ei_description': False,
                    'ei_events_ids': False})

        return True

    def action_manual_electronic_invoice(self, cr, uid, ids, context=None):
        return {
            'context': context,
            'type': 'ir.actions.act_window',
            'res_model': 'electronic.invoice.manual',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new'
        }


electronic_invoice()


class electronic_invoice_manual(osv.osv):
    _name = 'electronic.invoice.manual'
    _columns = {
        'ei_status': fields.char('EI Status', readonly=True),
        'ei_date': fields.date('EI Date'),
        'ei_code': fields.char('EI Code'),
        'ei_verification_code': fields.char('EI Verification Code')
    }

    def save_data(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids)[0]
        self.pool.get('account.invoice').write(
            cr, uid, context['active_id'], {
                'ei_status': 'confirmed',
                'ei_date': data['ei_date'],
                'ei_code': data['ei_code'],
                'ei_verification_code': data['ei_verification_code']
                }
        )
        self.pool.get('electronic.invoice.event').create(
            cr, uid, {
                'action': 'send',
                'message': u'NF-e criada manualmente',
                'invoice_id': context['active_id']
                }
        )
        return True
