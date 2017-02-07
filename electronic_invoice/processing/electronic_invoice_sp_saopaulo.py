# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from osv import fields, osv
from pysped_nfse.processador_sp import ProcessadorNFSeSP
import datetime
import urllib2
import pytz
import re
from openerp.tools.translate import _


class ei_sp_saopaulo_001(osv.osv):
    _name = 'ei.sp.saopaulo.001'
    VERSION = '1'

    def _spe_char_remove(self, text):
        if not text:
            return text
        text = text.encode('utf-8')
        if not text:
            return text == ''
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
            '\xc3\x87': 'C',
            '&': 'e'}
        for s, r in dic.iteritems():
            text = text.replace(s, r)

        return re.sub('[^a-zA-Z0-9/&. -]', '', text)

    def _check_server(self, cr, uid, ids, server_host):
        server_up = False
        if not server_host.startswith('http'):
            server_host = 'https://' + server_host
        try:
            if urllib2.urlopen(server_host).getcode() == 200:
                server_up = True
        except urllib2.HTTPError:
            server_up = False

        return server_up

    def validate_send(self, cr, uid, ids, inv, context=None):
        if not inv.company_id.tributacao:
            return '%s - %s' % (
                u'Tipo de Tributação não informada', inv.company_id.name)
        codigo_servico = False
        aliquota = False
        for inv_line in inv.invoice_line:
            if not codigo_servico or not aliquota:
                codigo_servico = inv_line.product_id.service_type_id and inv_line.product_id.service_type_id.code or ''
                aliquota = inv_line.issqn_percent
            else:
                if codigo_servico != inv_line.product_id.service_type_id.code:
                    return u'Não é permitido Códigos de Serviços diferentes na mesma NF'
                if aliquota != inv_line.issqn_percent:
                    return u'Não é permitido Alíquotas de ISS Diferentes na mesma NF'

        return ''

    def define_send(self, cr, uid, ids, inv, context=None):
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(
            pytz.timezone(user_timezone)).strftime('%Y-%m-%d')
        impostos = ('pis', 'cofins', 'inss', 'irpj', 'csll', 'issqn',
                    'iss_retido')
        valores = {x:0 for x in impostos}
        for inv_tax in inv.tax_line:
            if inv_tax.tax_code_id.domain in impostos and inv_tax.tax_retain:
                valores[inv_tax.tax_code_id.domain] += round(
                    inv_tax.tax_retain, 2)

        iss_retido = valores['iss_retido'] < 0
        account_invoice_line = inv.invoice_line[0]
        codigo_servico = account_invoice_line.product_id.service_type_id and account_invoice_line.product_id.service_type_id.code or ''
        aliquota = account_invoice_line.issqn_percent
        discriminacao = account_invoice_line.product_id.service_type_id and account_invoice_line.product_id.service_type_id.ei_description or ''
        discriminacao += inv.partner_id.ei_service_description and '\n' + inv.partner_id.ei_service_description or ''
        discriminacao += inv.ei_description and '\n' + inv.ei_description or ''
        discriminacao += inv.company_id.ei_service_description and '\n' + inv.company_id.ei_service_description or ''
        city_ibge_code = str(inv.partner_id.state_id.ibge_code) + str(inv.partner_id.l10n_br_city_id.ibge_code)
        lote_rps = []
        if inv.rps_code:
            rps_code = inv.rps_code
        else:
            raise osv.except_osv(_('Error'), _('Invoice without RPS Number'))
        lote_rps.append({
            'TipoRPS': 'RPS',
            'DataEmissao': date_now,
            'StatusRPS': 'N',
            'TributacaoRPS': inv.company_id.tributacao,
            'ValorServicos': inv.amount_untaxed,
            'ValorDeducoes': inv.amount_tax,
            'ValorPIS': valores['pis'],
            'ValorCOFINS': valores['cofins'],
            'ValorINSS': valores['inss'],
            'ValorIR': valores['irpj'],
            'ValorCSLL': valores['csll'],
            'CodigoServico': int(codigo_servico),
            'AliquotaServicos': round(aliquota / 100, 2),
            'ISSRetido': iss_retido,
            'CPFCNPJTomador': re.sub('[^0-9]', '', inv.partner_id.cnpj_cpf),
            'TipoInscricaoTomador': 'J' if inv.partner_id.is_company else 'F',
            'RazaoSocialTomador': unicode(self._spe_char_remove(
                inv.partner_id.legal_name) or '')[:75],
            'Logradouro': unicode(self._spe_char_remove(
                inv.partner_id.street) or '')[:50],
            'NumeroEndereco': inv.partner_id.number,
            'ComplementoEndereco': unicode(self._spe_char_remove(
                inv.partner_id.street2) or '')[:30],
            'Bairro': unicode(self._spe_char_remove(
                inv.partner_id.district) or '')[:30],
            'Cidade': city_ibge_code,
            'UF': inv.partner_id.state_id and inv.partner_id.state_id.code or '',
            'CEP': inv.partner_id.zip,
            'EmailTomador': (inv.partner_id.email or '')[:75],
            'Discriminacao': (discriminacao or '')[:2000],
            'SerieRPS': int(inv.document_serie_id.code),
            'NumeroRPS': rps_code})
        cabecalho = {
            'CPFCNPJRemetente': re.sub('[^0-9]', '', inv.company_id.cnpj_cpf),
            'InscricaoMunicipalPrestador': re.sub('[^0-9]', '',
                                                  inv.company_id.inscr_mun),
            'transacao': True,
            'dtInicio': date_now,
            'dtFim': date_now,
            'QtdRPS': len(lote_rps),
            'ValorTotalServicos': inv.amount_untaxed,
            'ValorTotalDeducoes': inv.amount_tax,
            'Versao': self.VERSION
        }
        return (lote_rps, cabecalho)

    def define_consult(self, cr, uid, ids, inv, context=None):
        consulta_rps = {
            'CPFCNPJRemetente': re.sub('[^0-9]', '', inv.company_id.cnpj_cpf),
            'InscricaoPrestador': re.sub('[^0-9]', '',
                                         inv.company_id.inscr_mun),
            'SerieRPS': int(inv.document_serie_id.code),
            'NumeroRPS': inv.rps_code,
            'Versao': self.VERSION
        }
        return consulta_rps

    def xml_send(self, cr, uid, ids, inv, lote_rps, cabecalho_rps,
                 consulta_rps, cert_name, context = None):
        cert_password = str(inv.company_id.nfe_a1_password)
        proc = ProcessadorNFSeSP(cert_name, cert_password)
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(
            pytz.timezone(user_timezone)).strftime('%Y-%m-%d')
        if datetime.datetime.now() > proc._certificado._data_fim_validade:
            return {'action': 'send',
                    'ei_status': 'failed',
                    'message': '%s - %s' % (
                        u'Certificado Digital fora da validade',
                        inv.company_id.name)}
        # if not self._check_server(cr, uid, ids, proc.servidor):
        #    return {
        #        'action': 'send',
        #        'ei_status': 'failed',
        #        'message': u'Falha de comunicação com o servidor'}
        if inv.company_id.ei_environment == 'production':
            success, res, warnings, errors = proc.consultar_nfse(consulta_rps)
            if success and not res.NFe:
                success, res, warnings, errors = proc.enviar_lote_rps(
                    cabecalho=cabecalho_rps, lote_rps=lote_rps)
        else:
            success, res, warnings, errors = proc.testar_envio_lote_rps(
                cabecalho=cabecalho_rps, lote_rps=lote_rps)
        msg_alerta = ''
        for alerta_line in res.Alerta:
            msg_alerta += '%s-%s\n' % (str(alerta_line.Codigo or 0),
                                       alerta_line.Descricao or '')

        msg_erro = ''
        for erro_line in res.Erro:
            msg_erro += '%s-%s\n' % (str(erro_line.Codigo or 0),
                                     erro_line.Descricao or '')

        w_chave_nfe = False
        chave_write = False
        if hasattr(res, 'NFe'):
            w_chave_nfe = res.NFe
        elif hasattr(res, 'ChaveNFeRPS'):
            w_chave_nfe = res.ChaveNFeRPS
        for chave_line in w_chave_nfe:
            if chave_line.ChaveNFe:
                chave_write = {
                    'ei_code': chave_line.ChaveNFe.NumeroNFe,
                    'ei_verification_code': chave_line.ChaveNFe.CodigoVerificacao,
                    'ei_date': date_now,
                    'rps_serie': int(inv.document_serie_id.code),
                    'rps_code': lote_rps[0]['NumeroRPS']}
                message = 'Nf-e sent'
                self.log(cr, uid, inv, message, context=context)

        if inv.company_id.ei_environment == 'production':
            if msg_erro:
                result = {
                    'action': 'send',
                    'ei_status': 'failed',
                    'message': '%s%s' % (msg_alerta, msg_erro)
                }
            elif not chave_write:
                result = {
                    'action': 'send',
                    'ei_status': 'sent',
                    'message': '%s%s' % (
                        msg_alerta,
                        u'NF-e enviada com SUCESSO, aguardando confirmação')}
            else:
                result = {
                    'action': 'send',
                    'ei_status': 'confirmed',
                    'message': '%s%s' % (msg_alerta,
                                         u'NF-e criada com SUCESSO')}
                result.update(chave_write)
        elif inv.company_id.ei_environment == 'test':
            if msg_erro:
                result = {
                    'action': 'send',
                    'message': '%s%s' % (msg_alerta, msg_erro)}
            else:
                result = {
                    'action': 'send',
                    'message': '%s%s' % (
                        msg_alerta,
                        u'Teste de envio de NF-e efetuado com SUCESSO')}
        return result

    def validate_cancel(self, cr, uid, ids, inv, context=None):
        if not inv.ei_code or not inv.ei_verification_code:
            return '%s - %s' % (
                u'Chave da NF-e não encontrada - ', inv.company_id.name)
        return ''

    def define_cancel(self, cr, uid, ids, inv, context=None):
        cancel_rps = {
            'CPFCNPJRemetente': re.sub('[^0-9]', '', inv.company_id.cnpj_cpf),
            'InscricaoPrestador': re.sub('[^0-9]', '',
                                         inv.company_id.inscr_mun),
            'NumeroNFe': inv.ei_code,
            'CodigoVerificacao': inv.ei_verification_code,
            'Versao': self.VERSION
        }
        return cancel_rps

    def xml_cancel(self, cr, uid, ids, inv, cancel_rps, cert_name,
                   context=None):
        cert_password = str(inv.company_id.nfe_a1_password)
        proc = ProcessadorNFSeSP(cert_name, cert_password)
        if datetime.datetime.now() > proc._certificado._data_fim_validade:
            return {
                'action': 'cancel',
                'message': '%s - %s' % (
                    u'Certificado Digital fora da validade',
                    inv.company_id.name)}
        if not self._check_server(cr, uid, ids, proc.servidor):
            return {
                'action': 'cancel',
                'message': u'Falha de comunicação com o servidor'}
        if inv.company_id.ei_environment == 'production':
            success, res, warnings, errors = proc.cancelar_nfse(cancel_rps)
        else:
            return {
                'action': 'cancel',
                'message': u'Serviço de Teste para Cancelamento INDISPONÍVEL'
            }
        msg_alerta = ''
        for alerta_line in res.Alerta:
            msg_alerta += '%s-%s\n' % (str(alerta_line.Codigo or 0),
                                       alerta_line.Descricao or '')

        msg_erro = ''
        for erro_line in res.Erro:
            msg_erro += '%s-%s\n' % (str(erro_line.Codigo or 0),
                                     erro_line.Descricao or '')

        if msg_erro:
            result = {
                'action': 'cancel',
                'message': '%s%s' % (msg_alerta, msg_erro)
            }
        else:
            result = {
                'action': 'cancel',
                'ei_status': 'cancelled',
                'message': '%s%s' % (msg_alerta, u'NF-e cancelada com SUCESSO')
            }
        return result


ei_sp_saopaulo_001()


class electronic_invoice(osv.osv):
    _inherit = 'electronic.invoice'

    def send_sp_saopaulo(self, cr, uid, ids, inv, cert_name, context = None):
        if inv.company_id.ei_service_version == '05030_1':
            ei_service_obj = self.pool.get('ei.sp.saopaulo.001')
        else:
            return {
                'action': 'send',
                'ei_status': 'failed',
                'message': u'Versão de NF-e não disponível'
            }
        msg = ei_service_obj.validate_send(cr, uid, ids, inv, context=context)
        if msg:
            return {
                'action': 'send',
                'ei_status': 'failed',
                'message': msg
            }
        else:
            lote_rps, cabecalho_rps = ei_service_obj.define_send(
                cr, uid, ids, inv, context=None)
            consulta_rps = ei_service_obj.define_consult(
                cr, uid, ids, inv, context=None)
            result = ei_service_obj.xml_send(
                cr, uid, ids, inv, lote_rps, cabecalho_rps, consulta_rps,
                cert_name, context=None)
            return result

    def cancel_sp_saopaulo(self, cr, uid, ids, inv, cert_name, context=None):
        if inv.company_id.ei_service_version == '05030_1':
            ei_service_obj = self.pool.get('ei.sp.saopaulo.001')
        else:
            return {
                'action': 'cancel',
                'message': 'Versão de NF-e não disponível'
            }
        msg = ei_service_obj.validate_cancel(cr, uid, ids, inv, context=None)
        if msg:
            return {
                'action': 'cancel',
                'message': msg
            }
        else:
            cancel_rps = ei_service_obj.define_cancel(
                cr, uid, ids, inv, context=None)
            result = ei_service_obj.xml_cancel(
                cr, uid, ids, inv, cancel_rps, cert_name, context=None)
            return result

    def inactivate_sp_saopaulo(self, cr, uid, ids, invoice, cert_name,
                               context=None):
        result = {'ei_status': 'inactive'}
        return result


electronic_invoice()
