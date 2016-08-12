# Embedded file name: /opt/openerp/homolog/addons-extra/electronic_invoice/processing/electronic_invoice_product.py
from osv import fields, osv
import datetime
import pytz
import re
import os
import string
import base64
from uuid import uuid4
from pysped.nfe.leiaute import NFe_310, Det_310, NFRef_310, Dup_310, EventoCancNFe_100, EventoCCe_100, AutXML_310
from pysped.nfe import ProcessadorNFe

class ei_product_310(osv.osv):
    _name = 'ei.product.310'

    def validate_send(self, cr, uid, ids, inv, context = None):
        if not inv.company_id.ei_product_version:
            return '%s - %s' % (u'Vers\xe3o da NF-e n\xe3o informada -', inv.company_id.name)
        if inv.carrier_id and not inv.carrier_id.partner_id:
            return '%s - %s' % (u'Dados da Trasportadora n\xe3o informados ', inv.carrier_id.name)
        return ''

    def define_send(self, cr, uid, ids, inv, context = None):
        if not context:
            context = {'lang': 'pt_BR'}
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(pytz.timezone(user_timezone))
        nfe = NFe_310()
        tp_amb = 1 if inv.company_id.ei_environment == 'production' else 2
        tp_nf = '1'
        if inv.cfop_ids[0].type in 'input':
            tp_nf = '0'
        if inv.partner_id.country_id.id != inv.company_id.partner_id.country_id.id:
            idDest = '3'
        elif inv.partner_id.state_id.code == inv.company_id.partner_id.state_id.code:
            idDest = '1'
        else:
            idDest = '2'
        nfe.infNFe.ide.cUF.valor = inv.company_id.partner_id.state_id and inv.company_id.partner_id.state_id.ibge_code or ''
        nfe.infNFe.ide.cNF.valor = ''
        nfe.infNFe.ide.natOp.valor = inv.cfop_ids[0].small_name or ''
        nfe.infNFe.ide.indPag.valor = inv.payment_term and inv.payment_term.indPag or '0'
        nfe.infNFe.ide.mod.valor = inv.document_serie_id and inv.document_serie_id.fiscal_document_id and inv.document_serie_id.fiscal_document_id.code or ''
        nfe.infNFe.ide.serie.valor = inv.document_serie_id and inv.document_serie_id.code or ''
        nfe.infNFe.ide.nNF.valor = inv.internal_number or ''
        nfe.infNFe.ide.dEmi.valor = inv.date_invoice or ''
        nfe.infNFe.ide.dhEmi.valor = date_now or ''
        nfe.infNFe.ide.dSaiEnt.valor = inv.date_invoice or ''
        nfe.infNFe.ide.cMunFG.valor = '%s%s' % (inv.company_id.partner_id.state_id.ibge_code, inv.company_id.partner_id.l10n_br_city_id.ibge_code)
        nfe.infNFe.ide.tpImp.valor = 1
        nfe.infNFe.ide.tpEmis.valor = 1
        nfe.infNFe.ide.tpAmb.valor = tp_amb
        nfe.infNFe.ide.finNFe.valor = inv.nfe_purpose
        nfe.infNFe.ide.procEmi.valor = 0
        nfe.infNFe.ide.verProc.valor = 'OpenERP Brasil v7'
        nfe.infNFe.ide.tpNF.valor = tp_nf
        nfe.infNFe.ide.idDest.valor = idDest
        if inv.partner_shipping_id:
            if inv.partner_id.id != inv.partner_shipping_id.id:
                if nfe.infNFe.ide.tpNF.valor == '0':
                    nfe.infNFe.retirada.CNPJ.valor = inv.partner_shipping_id.cnpj_cpf or ''
                    nfe.infNFe.retirada.xLgr.valor = inv.partner_shipping_id.street or ''
                    nfe.infNFe.retirada.nro.valor = inv.partner_shipping_id.number or ''
                    nfe.infNFe.retirada.xCpl.valor = inv.partner_shipping_id.street2 or ''
                    nfe.infNFe.retirada.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                    nfe.infNFe.retirada.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                    nfe.infNFe.retirada.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                    nfe.infNFe.retirada.UF.valor = inv.address_invoice_id.state_id.code or ''
                else:
                    nfe.infNFe.entrega.CNPJ.valor = inv.partner_shipping_id.cnpj_cpf or ''
                    nfe.infNFe.entrega.xLgr.valor = inv.partner_shipping_id.street or ''
                    nfe.infNFe.entrega.nro.valor = inv.partner_shipping_id.number or ''
                    nfe.infNFe.entrega.xCpl.valor = inv.partner_shipping_id.street2 or ''
                    nfe.infNFe.entrega.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                    nfe.infNFe.entrega.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                    nfe.infNFe.entrega.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                    nfe.infNFe.entrega.UF.valor = inv.address_invoice_id.state_id.code or ''
        for inv_related in inv.fiscal_document_related_ids:
            nfref = NFRef_310()
            if inv_related.document_type == 'nf':
                nfref.refNF.cUF.valor = (inv_related.state_id and inv_related.state_id.ibge_code or '',)
                nfref.refNF.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
                nfref.refNF.CNPJ.valor = inv_related.cnpj_cpf or ''
                nfref.refNF.Mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                nfref.refNF.serie.valor = inv_related.serie or ''
                nfref.refNF.nNF.valor = inv_related.internal_number or ''
            elif inv_related.document_type == 'nfrural':
                nfref.refNFP.cUF.valor = (inv_related.state_id and inv_related.state_id.ibge_code or '',)
                nfref.refNFP.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
                nfref.refNFP.IE.valor = inv_related.inscr_est or ''
                nfref.refNFP.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                nfref.refNFP.serie.valor = inv_related.serie or ''
                nfref.refNFP.nNF.valor = inv_related.internal_number or ''
                if inv_related.cpfcnpj_type == 'cnpj':
                    nfref.refNFP.CNPJ.valor = inv_related.cnpj_cpf or ''
                else:
                    nfref.refNFP.CPF.valor = inv_related.cnpj_cpf or ''
            elif inv_related.document_type == 'nfe':
                nfref.refNFe.valor = inv_related.access_key or ''
            elif inv_related.document_type == 'cte':
                nfref.refCTe.valor = inv_related.access_key or ''
            elif inv_related.document_type == 'cf':
                nfref.refECF.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                nfref.refECF.nECF.valor = inv_related.internal_number
                nfref.refECF.nCOO.valor = inv_related.serie

        nfe.infNFe.emit.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or '')
        nfe.infNFe.emit.xNome.valor = inv.company_id.partner_id.legal_name
        nfe.infNFe.emit.xFant.valor = inv.company_id.partner_id.name
        nfe.infNFe.emit.enderEmit.xLgr.valor = inv.company_id.partner_id.street or ''
        nfe.infNFe.emit.enderEmit.nro.valor = inv.company_id.partner_id.number or ''
        nfe.infNFe.emit.enderEmit.xCpl.valor = inv.company_id.partner_id.street2 or ''
        nfe.infNFe.emit.enderEmit.xBairro.valor = inv.company_id.partner_id.district or 'Sem Bairro'
        nfe.infNFe.emit.enderEmit.cMun.valor = '%s%s' % (inv.company_id.partner_id.state_id.ibge_code, inv.company_id.partner_id.l10n_br_city_id.ibge_code)
        nfe.infNFe.emit.enderEmit.xMun.valor = inv.company_id.partner_id.l10n_br_city_id.name or ''
        nfe.infNFe.emit.enderEmit.UF.valor = inv.company_id.partner_id.state_id.code or ''
        nfe.infNFe.emit.enderEmit.CEP.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.company_id.partner_id.zip or '').replace(' ', ''))
        nfe.infNFe.emit.enderEmit.cPais.valor = inv.company_id.partner_id.country_id.bc_code[1:]
        nfe.infNFe.emit.enderEmit.xPais.valor = inv.company_id.partner_id.country_id.name
        nfe.infNFe.emit.enderEmit.fone.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.company_id.partner_id.phone or '').replace(' ', ''))
        nfe.infNFe.emit.IE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_est or '')
        nfe.infNFe.emit.IEST.valor = ''
        nfe.infNFe.emit.IM.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_mun or '')
        nfe.infNFe.emit.CRT.valor = inv.company_id.fiscal_type or ''
        if inv.company_id.partner_id.inscr_mun:
            nfe.infNFe.emit.CNAE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.cnae_main_id.code or '')
        partner_bc_code = ''
        if inv.partner_id.country_id.bc_code:
            partner_bc_code = inv.partner_id.country_id.bc_code[1:]
        address_invoice_state_code = inv.partner_id.state_id.code
        address_invoice_city = inv.partner_id.l10n_br_city_id.name or ''
        partner_cep = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.partner_id.zip or '').replace(' ', ''))
        if inv.partner_id.country_id.id != inv.company_id.partner_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            partner_cep = ''
        nfe.infNFe.dest.xNome.valor = inv.partner_id.legal_name or ''
        if tp_amb == 2:
            nfe.infNFe.dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
        if inv.partner_id.is_company:
            nfe.infNFe.dest.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or '')
            nfe.infNFe.dest.IE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.inscr_est or '')
        else:
            nfe.infNFe.dest.CPF.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or '')
        nfe.infNFe.dest.indIEDest.valor = inv.partner_id.partner_fiscal_type_id.code
        nfe.infNFe.dest.enderDest.xLgr.valor = inv.partner_id.street or ''
        nfe.infNFe.dest.enderDest.nro.valor = inv.partner_id.number or ''
        nfe.infNFe.dest.enderDest.xCpl.valor = inv.partner_id.street2 or ''
        nfe.infNFe.dest.enderDest.xBairro.valor = inv.partner_id.district or 'Sem Bairro'
        nfe.infNFe.dest.enderDest.cMun.valor = '%s%s' % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
        nfe.infNFe.dest.enderDest.xMun.valor = address_invoice_city
        nfe.infNFe.dest.enderDest.UF.valor = address_invoice_state_code
        nfe.infNFe.dest.enderDest.CEP.valor = partner_cep
        nfe.infNFe.dest.enderDest.cPais.valor = partner_bc_code
        nfe.infNFe.dest.enderDest.xPais.valor = inv.partner_id.country_id.name or ''
        nfe.infNFe.dest.enderDest.fone.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.partner_id.phone or '').replace(' ', ''))
        nfe.infNFe.dest.email.valor = inv.partner_id.email or ''
        aut_xml = AutXML_310()
        if inv.company_id.accounting_responsible.cnpj_cpf:
            if inv.company_id.accounting_responsible.is_company:
                aut_xml.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.accounting_responsible.cnpj_cpf or '')
            else:
                aut_xml.CPF.valor = inv.company_id.accounting_responsible.cnpj_cpf
        nfe.infNFe.autXML.append(aut_xml)
        total_items = len(inv.invoice_line)
        i = 0
        total_disc_item = 0
        total_disc_without_last_item = 0
        for inv_line in inv.invoice_line:
            i += 1
            det = Det_310()
            total_disc_item += inv_line.discount_value
            det.nItem.valor = i
            det.prod.cProd.valor = inv_line.product_id.code or ''
            det.prod.cEAN.valor = inv_line.product_id.ean13 or ''
            det.prod.xProd.valor = inv_line.product_id.name or ''
            det.prod.NCM.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_line.fiscal_classification_id.name or '')
            det.prod.EXTIPI.valor = ''
            det.prod.CFOP.valor = inv_line.cfop_id.code
            det.prod.uCom.valor = inv_line.uos_id.name or ''
            det.prod.qCom.valor = str('%.4f' % inv_line.quantity)
            det.prod.vUnCom.valor = str('%.7f' % inv_line.price_unit)
            det.prod.vProd.valor = str('%.2f' % inv_line.price_gross)
            det.prod.cEANTrib.valor = inv_line.product_id.ean13 or ''
            det.prod.uTrib.valor = det.prod.uCom.valor
            det.prod.qTrib.valor = det.prod.qCom.valor
            det.prod.vUnTrib.valor = det.prod.vUnCom.valor
            det.prod.vFrete.valor = str('%.2f' % inv_line.freight_value)
            det.prod.vSeg.valor = str('%.2f' % inv_line.insurance_value)
            if i != total_items:
                det.prod.vDesc.valor = str('%.2f' % inv_line.discount_value)
                total_disc_without_last_item += float(str('%.2f' % inv_line.discount_value))
            else:
                value_disc = float(str('%.2f' % total_disc_item)) - total_disc_without_last_item
                det.prod.vDesc.valor = str('%.2f' % value_disc)
            det.prod.vOutro.valor = str('%.2f' % inv_line.other_costs_value)
            det.prod.indTot.valor = 1
            if inv_line.product_type == 'product':
                if inv_line.icms_cst_id.code > 100:
                    det.imposto.ICMS.CSOSN.valor = inv_line.icms_cst_id.code
                    det.imposto.ICMS.pCredSN.valor = str('%.2f' % inv_line.icms_percent)
                    det.imposto.ICMS.vCredICMSSN.valor = str('%.2f' % inv_line.icms_value)
                det.imposto.ICMS.CST.valor = inv_line.icms_cst_id.code
                det.imposto.ICMS.modBC.valor = inv_line.icms_base_type
                det.imposto.ICMS.vBC.valor = str('%.2f' % inv_line.icms_base)
                det.imposto.ICMS.pRedBC.valor = str('%.2f' % inv_line.icms_percent_reduction)
                det.imposto.ICMS.pICMS.valor = str('%.2f' % inv_line.icms_percent)
                det.imposto.ICMS.vICMS.valor = str('%.2f' % inv_line.icms_value)
                det.imposto.ICMS.modBCST.valor = inv_line.icms_st_base_type
                det.imposto.ICMS.pMVAST.valor = str('%.2f' % inv_line.icms_st_mva)
                det.imposto.ICMS.pRedBCST.valor = str('%.2f' % inv_line.icms_st_percent_reduction)
                det.imposto.ICMS.vBCST.valor = str('%.2f' % inv_line.icms_st_base)
                det.imposto.ICMS.pICMSST.valor = str('%.2f' % inv_line.icms_st_percent)
                det.imposto.ICMS.vICMSST.valor = str('%.2f' % inv_line.icms_st_value)
                det.imposto.IPI.CST.valor = inv_line.ipi_cst_id.code
                det.imposto.IPI.vBC.valor = str('%.2f' % inv_line.ipi_base)
                det.imposto.IPI.pIPI.valor = str('%.2f' % inv_line.ipi_percent)
                det.imposto.IPI.vIPI.valor = str('%.2f' % inv_line.ipi_value)
            else:
                det.imposto.ISSQN.vBC.valor = str('%.2f' % inv_line.issqn_base)
                det.imposto.ISSQN.vAliq.valor = str('%.2f' % inv_line.issqn_percent)
                det.imposto.ISSQN.vISSQN.valor = str('%.2f' % inv_line.issqn_value)
                det.imposto.ISSQN.cMunFG.valor = '%s%s' % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
                det.imposto.ISSQN.cListServ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_line.service_type_id.code or '')
                det.imposto.ISSQN.cSitTrib.valor = inv_line.issqn_type
            det.imposto.PIS.CST.valor = inv_line.pis_cst_id.code
            det.imposto.PIS.vBC.valor = str('%.2f' % inv_line.pis_base)
            det.imposto.PIS.pPIS.valor = str('%.2f' % inv_line.pis_percent)
            det.imposto.PIS.vPIS.valor = str('%.2f' % inv_line.pis_value)
            det.imposto.PISST.vBC.valor = str('%.2f' % inv_line.pis_st_base)
            det.imposto.PISST.pPIS.valor = str('%.2f' % inv_line.pis_st_percent)
            det.imposto.PISST.qBCProd.valor = ''
            det.imposto.PISST.vAliqProd.valor = ''
            det.imposto.PISST.vPIS.valor = str('%.2f' % inv_line.pis_st_value)
            det.imposto.COFINS.CST.valor = inv_line.cofins_cst_id.code
            det.imposto.COFINS.vBC.valor = str('%.2f' % inv_line.cofins_base)
            det.imposto.COFINS.pCOFINS.valor = str('%.2f' % inv_line.cofins_percent)
            det.imposto.COFINS.vCOFINS.valor = str('%.2f' % inv_line.cofins_value)
            det.imposto.COFINSST.vBC.valor = str('%.2f' % inv_line.cofins_st_base)
            det.imposto.COFINSST.pCOFINS.valor = str('%.2f' % inv_line.cofins_st_percent)
            det.imposto.COFINSST.qBCProd.valor = ''
            det.imposto.COFINSST.vAliqProd.valor = ''
            det.imposto.COFINSST.vCOFINS.valor = str('%.2f' % inv_line.cofins_st_value)
            nfe.infNFe.det.append(det)

        if inv.journal_id.revenue_expense:
            for line in inv.move_line_receivable_id:
                dup = Dup_310()
                dup.nDup.valor = line.name
                dup.dVenc.valor = line.date_maturity or inv.date_due or inv.date_invoice
                dup.vDup.valor = str('%.2f' % line.debit)
                nfe.infNFe.cobr.dup.append(dup)

        if inv.carrier_id:
            nfe.infNFe.transp.modFrete.valor = inv.incoterm and inv.incoterm.freight_responsibility or '9'
            if inv.carrier_id.partner_id.is_company:
                nfe.infNFe.transp.transporta.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.carrier_id.partner_id.cnpj_cpf or '')
            else:
                nfe.infNFe.transp.transporta.CPF.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.carrier_id.partner_id.cnpj_cpf or '')
            nfe.infNFe.transp.transporta.xNome.valor = inv.carrier_id.partner_id.legal_name or ''
            nfe.infNFe.transp.transporta.IE.valor = inv.carrier_id.partner_id.inscr_est or ''
            nfe.infNFe.transp.transporta.xEnder.valor = inv.carrier_id.partner_id.street or ''
            nfe.infNFe.transp.transporta.xMun.valor = inv.carrier_id.partner_id.l10n_br_city_id.name or ''
            nfe.infNFe.transp.transporta.UF.valor = inv.carrier_id.partner_id.state_id.code or ''
        if inv.vehicle_id:
            nfe.infNFe.transp.veicTransp.placa.valor = inv.vehicle_id.plate or ''
            nfe.infNFe.transp.veicTransp.UF.valor = inv.vehicle_id.plate.state_id.code or ''
            nfe.infNFe.transp.veicTransp.RNTC.valor = inv.vehicle_id.rntc_code or ''
        nfe.infNFe.infAdic.infAdFisco.valor = ''
        nfe.infNFe.infAdic.infCpl.valor = inv.comment or ''
        nfe.infNFe.total.ICMSTot.vBC.valor = str('%.2f' % inv.icms_base)
        nfe.infNFe.total.ICMSTot.vICMS.valor = str('%.2f' % inv.icms_value)
        nfe.infNFe.total.ICMSTot.vBCST.valor = str('%.2f' % inv.icms_st_base)
        nfe.infNFe.total.ICMSTot.vST.valor = str('%.2f' % inv.icms_st_value)
        nfe.infNFe.total.ICMSTot.vProd.valor = str('%.2f' % inv.amount_gross)
        nfe.infNFe.total.ICMSTot.vFrete.valor = str('%.2f' % inv.amount_freight)
        nfe.infNFe.total.ICMSTot.vSeg.valor = str('%.2f' % inv.amount_insurance)
        nfe.infNFe.total.ICMSTot.vDesc.valor = str('%.2f' % inv.amount_discount)
        nfe.infNFe.total.ICMSTot.vII.valor = str('%.2f' % inv.ii_value)
        nfe.infNFe.total.ICMSTot.vIPI.valor = str('%.2f' % inv.ipi_value)
        nfe.infNFe.total.ICMSTot.vPIS.valor = str('%.2f' % inv.pis_value)
        nfe.infNFe.total.ICMSTot.vCOFINS.valor = str('%.2f' % inv.cofins_value)
        nfe.infNFe.total.ICMSTot.vOutro.valor = str('%.2f' % inv.amount_costs)
        nfe.infNFe.total.ICMSTot.vNF.valor = str('%.2f' % inv.amount_total)
        nfe.gera_nova_chave()
        return nfe

    def xml_send(self, cr, uid, ids, inv, ei_obj, cert_name, context = None):
        proc_nfe = ProcessadorNFe()
        proc_nfe.ambiente = 1 if inv.company_id.ei_environment == 'production' else 2
        proc_nfe.versao = '3.10'
        proc_nfe.estado = inv.company_id.partner_id.l10n_br_city_id.state_id.code
        proc_nfe.certificado.senha = inv.company_id.nfe_a1_password
        proc_nfe.certificado.arquivo = cert_name
        proc_nfe.salvar_arquivos = False
        for processo in proc_nfe.processar_notas([ei_obj]):
            result = {'action': 'send',
             'ei_status': 'failed',
             'message': processo.resposta.cStat.valor + '-' + processo.resposta.xMotivo.valor,
             'ei_access_key': ei_obj.chave}
            if processo.webservice == 1:
                for prot in processo.resposta.protNFe:
                    result['message'] = prot.infProt.cStat.valor + '-' + prot.infProt.xMotivo.valor
                    if prot.infProt.cStat.valor in ('100', '150'):
                        result['ei_protocol'] = prot.infProt.nProt.valor
                        result['ei_status'] = 'confirmed'
                        result['ei_date'] = prot.infProt.dhRecbto.valor
                        result['xml_send'] = ei_obj.xml
                        result['ei_image'] = proc_nfe.danfe.conteudo_pdf
                        result['ei_code'] = inv.internal_number

            elif processo.resposta.cStat.valor in ('100', '150'):
                result['ei_status'] = 'confirmed'
                result['ei_date'] = processo.resposta.protNFe.infProt.dhRecbto.valor
                result['ei_protocol'] = processo.resposta.protNFe.infProt.nProt.valor
                result['xml_send'] = ei_obj.xml
                result['ei_code'] = inv.internal_number

        return result

    def validate_cancel(self, cr, uid, ids, inv, context = None):
        if not inv.ei_access_key or not inv.ei_protocol:
            return '%s - %s' % (u'Chave da NF-e n\xe3o encontrada - ', inv.company_id.name)
        if not inv.ei_justification:
            return '%s' % u'Justificativa da NF-e n\xe3o encontrada'
        return ''

    def define_cancel(self, cr, uid, ids, inv, context = None):
        if not context:
            context = {'lang': 'pt_BR'}
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(pytz.timezone(user_timezone))
        nfe = EventoCancNFe_100()
        nfe.infEvento.tpAmb.valor = 1 if inv.company_id.ei_environment == 'production' else 2
        nfe.infEvento.cOrgao.valor = inv.company_id.partner_id.state_id.ibge_code
        nfe.infEvento.CNPJ.valor = inv.ei_access_key[6:20]
        nfe.infEvento.chNFe.valor = inv.ei_access_key
        nfe.infEvento.dhEvento.valor = date_now
        nfe.infEvento.detEvento.nProt.valor = inv.ei_protocol
        nfe.infEvento.detEvento.xJust.valor = inv.ei_justification
        return nfe

    def xml_cancel(self, cr, uid, ids, inv, ei_obj, cert_name, context = None):
        proc_nfe = ProcessadorNFe()
        proc_nfe.ambiente = 1 if inv.company_id.ei_environment == 'production' else 2
        proc_nfe.versao = '3.10'
        proc_nfe.estado = inv.company_id.partner_id.l10n_br_city_id.state_id.code
        proc_nfe.certificado.senha = inv.company_id.nfe_a1_password
        proc_nfe.certificado.arquivo = cert_name
        proc_nfe.salvar_arquivos = False
        processo = proc_nfe.enviar_lote_cancelamento(lista_eventos=[ei_obj])
        result = {'action': 'cancel',
         'message': processo.resposta.xMotivo.valor}
        for prot in processo.resposta.retEvento:
            result['message'] = prot.infEvento.cStat.valor + '-' + processo.resposta.xMotivo.valor
            if prot.infEvento.cStat.valor == '135':
                result.update({'ei_status': 'cancelled'})

        return result

    def validate_inactivate(self, cr, uid, ids, inv, context = None):
        if not inv.ei_justification:
            return '%s' % u'Justificativa da NF-e n\xe3o encontrada'
        return ''

    def define_inactivate(self, cr, uid, ids, inv, context = None):
        if not context:
            context = {'lang': 'pt_BR'}
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(pytz.timezone(user_timezone))
        nfe = {'ambiente': 1 if inv.company_id.ei_environment == 'production' else 2,
         'UF': inv.company_id.partner_id.state_id.ibge_code,
         'ano': date_now.strftime('%y'),
         'CNPJ/CPF': re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or ''),
         'serie': inv.document_serie_id.code,
         'numero_inicial': inv.internal_number,
         'numero_final': inv.internal_number,
         'justificativa': inv.ei_justification}
        return nfe

    def xml_inactivate(self, cr, uid, ids, inv, ei_obj, cert_name, context = None):
        proc_nfe = ProcessadorNFe()
        proc_nfe.ambiente = 1 if inv.company_id.ei_environment == 'production' else 2
        proc_nfe.versao = '3.10'
        proc_nfe.estado = inv.company_id.partner_id.l10n_br_city_id.state_id.code
        proc_nfe.certificado.senha = inv.company_id.nfe_a1_password
        proc_nfe.certificado.arquivo = cert_name
        proc_nfe.salvar_arquivos = False
        processo = proc_nfe.inutilizar_nota(ambiente=ei_obj['ambiente'], codigo_estado=ei_obj['UF'], ano=ei_obj['ano'], cnpj=ei_obj['CNPJ/CPF'], serie=ei_obj['serie'], numero_inicial=ei_obj['numero_inicial'], numero_final=ei_obj['numero_final'], justificativa=ei_obj['justificativa'])
        if processo.resposta.infInut.cStat.valor == '102':
            result = {'action': 'inactivate',
             'message': processo.resposta.infInut.xMotivo.valor,
             'ei_status': 'inactive'}
        else:
            msg = processo.resposta.infInut.cStat.valor + ' - ' + processo.resposta.xMotivo.valor
            result = {'action': 'inactivate',
             'message': msg}
        return result

    def define_correction_letter(self, cr, uid, ids, inv, context = None):
        if not context:
            context = {'lang': 'pt_BR'}
        user_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        date_now = datetime.datetime.now(pytz.timezone(user_timezone))
        nfe = EventoCCe_100()
        nfe.infEvento.tpAmb.valor = 1 if inv.company_id.ei_environment == 'production' else 2
        nfe.infEvento.cOrgao.valor = inv.company_id.partner_id.state_id.ibge_code
        nfe.infEvento.CNPJ.valor = inv.ei_access_key[6:20]
        nfe.infEvento.chNFe.valor = inv.ei_access_key
        nfe.infEvento.dhEvento.valor = date_now
        nfe.infEvento.detEvento.xCorrecao.valor = inv.ei_correction_letter
        nfe.infEvento.nSeqEvento.valor = inv.ei_correction_letter and 2 or 1
        return nfe

    def xml_correction_letter(self, cr, uid, ids, inv, ei_obj, cert_name, context = None):
        proc_nfe = ProcessadorNFe()
        proc_nfe.ambiente = 1 if inv.company_id.ei_environment == 'production' else 2
        proc_nfe.versao = '3.10'
        proc_nfe.estado = inv.company_id.partner_id.l10n_br_city_id.state_id.code
        proc_nfe.certificado.senha = inv.company_id.nfe_a1_password
        proc_nfe.certificado.arquivo = cert_name
        proc_nfe.salvar_arquivos = False
        processo = proc_nfe.enviar_lote_cce(lista_eventos=[ei_obj])
        if processo.resposta.cStat.valor == '128':
            result = {'action': 'correction_letter',
             'message': processo.resposta.xMotivo.valor}
        else:
            result = {'action': 'correction_letter',
             'message': '%s - %s' % (processo.resposta.cStat.valor, processo.resposta.xMotivo.valor)}
        return result


ei_product_310()

class electronic_invoice(osv.osv):
    _inherit = 'electronic.invoice'

    def send_product(self, cr, uid, ids, inv, cert_name, context = None):
        if inv.company_id.ei_product_version == '310':
            ei_product_obj = self.pool.get('ei.product.310')
        else:
            return {'action': 'send',
             'ei_status': 'failed',
             'message': 'Versao de NF-e nao disponivel'}
        msg = ei_product_obj.validate_send(cr, uid, ids, inv, context=context)
        if msg:
            return {'action': 'send',
             'message': msg,
             'ei_status': 'failed'}
        ei_obj = ei_product_obj.define_send(cr, uid, ids, inv, context=context)
        msg = ei_obj.validar()
        if msg:
            return {'action': 'send',
             'message': msg,
             'ei_status': 'failed'}
        result = ei_product_obj.xml_send(cr, uid, ids, inv, ei_obj, cert_name, context=context)
        return result

    def cancel_product(self, cr, uid, ids, inv, cert_name, context = None):
        if inv.company_id.ei_product_version == '310':
            ei_product_obj = self.pool.get('ei.product.310')
        else:
            return {'action': 'cancel',
             'message': 'Versao de NF-e nao disponivel'}
        msg = ei_product_obj.validate_cancel(cr, uid, ids, inv, context=context)
        if msg:
            return {'action': 'cancel',
             'message': msg}
        ei_obj = ei_product_obj.define_cancel(cr, uid, ids, inv, context=context)
        msg = ei_obj.validar()
        if msg:
            return {'action': 'cancel',
             'message': msg}
        result = ei_product_obj.xml_cancel(cr, uid, ids, inv, ei_obj, cert_name, context=context)
        return result

    def inactivate_product(self, cr, uid, ids, inv, cert_name, context = None):
        if inv.company_id.ei_product_version == '310':
            ei_product_obj = self.pool.get('ei.product.310')
        else:
            return {'action': 'inactivate',
             'message': 'Versao de NF-e nao disponivel'}
        msg = ei_product_obj.validate_inactivate(cr, uid, ids, inv, context=context)
        if msg:
            return {'action': 'inactivate',
             'message': msg}
        ei_obj = ei_product_obj.define_inactivate(cr, uid, ids, inv, context=context)
        result = ei_product_obj.xml_inactivate(cr, uid, ids, inv, ei_obj, cert_name, context=context)
        return result

    def correction_letter_product(self, cr, uid, ids, inv, cert_name, context = None):
        if inv.company_id.ei_product_version == '310':
            ei_product_obj = self.pool.get('ei.product.310')
        else:
            return {'action': 'correction_letter',
             'message': 'Versao de NF-e nao disponivel'}
        ei_obj = ei_product_obj.define_correction_letter(cr, uid, ids, inv, context=context)
        msg = ei_obj.validar()
        if msg:
            return {'action': 'correction_letter',
             'message': msg}
        result = ei_product_obj.xml_correction_letter(cr, uid, ids, inv, ei_obj, cert_name, context=context)
        return result


electronic_invoice()