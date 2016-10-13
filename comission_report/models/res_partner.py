# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import locale
from openerp.osv import osv, fields
from datetime import datetime


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'percentual_iss': fields.float('Percentual ISS'),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', string="Tipo Serviço"),
        'percentual_irrf': fields.float('Percentual IRRF'),
        'percentual_pcc': fields.float('Percentual PCC'),
    }

    def get_commission(self, cr, uid, ids, start_date, end_date, context=None):
        inicio = datetime.strptime(start_date, '%Y-%m-%d')
        final = datetime.strptime(end_date, '%Y-%m-%d')
        sql = "select cpcr.product_name, rp.cnpj_cpf, rp.legal_name, \
            ai.date_due, cpcr.date, cpcr.received, \
            cpcr.perc_commission, cpcr.value_commission \
            from contract_partner_commission_report cpcr \
            inner join res_partner rp on cpcr.customer_id = rp.id \
            inner join account_invoice ai on cpcr.invoice_id = ai.id \
            where cpcr.date between %s and %s \
            and cpcr.partner_id = %s and cpcr.state = 'paid' \
            order by cpcr.date"

        cr.execute(sql, (inicio, final, ids[0]))
        resultados = cr.fetchall()

        locale.setlocale(locale.LC_ALL, 'pt_BR')
        comissoes = [{
            'produto': x[0].replace(u'Licença de uso software', ''),
            'cnpj': x[1],
            'cliente': x[2],
            'vencimento': x[3],
            'pagamento': x[4],
            'mensalidade': locale.format_string("R$ %.2f", x[5]),
            'percentual': locale.format_string("%.0f%%", x[6]),
            'valor': locale.format_string("R$ %.2f", x[7]),
            'valor_decimal': x[7],
        } for x in resultados]
        bruto = sum(x['valor_decimal'] for x in comissoes)

        partner = self.browse(cr, uid, ids[0], context)
        irrf = (bruto * partner.percentual_irrf / 100) if bruto > 666.40 else 0.0
        pcc = (bruto * partner.percentual_pcc / 100) if bruto > 215 else 0.0
        impostos = {'iss': locale.format_string(
                        "%.2f", (bruto * partner.percentual_iss / 100)),
                    'perc_iss': locale.format_string(
                        "%.2f", (partner.percentual_iss)),
                    'irrf': locale.format_string(
                        "%.2f", irrf),
                    'perc_irrf': locale.format_string(
                        "%.2f", (partner.percentual_irrf)),
                    'pcc': locale.format_string(
                        "%.2f", pcc),
                    'perc_pcc': locale.format_string(
                        "%.2f", (partner.percentual_pcc))}

        liquido = bruto - round(bruto * partner.percentual_iss / 100, 2)
        liquido -= round(bruto * partner.percentual_irrf / 100, 2)
        liquido -= round(bruto * partner.percentual_pcc / 100, 2)

        impostos['total'] = bruto - liquido

        bruto = locale.format_string("%.2f", bruto)
        liquido = locale.format_string("%.2f", liquido)
        return comissoes, bruto, impostos, liquido
