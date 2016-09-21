# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import shutil
import base64
import zipfile
import os.path
from openerp.osv import fields, osv
from datetime import datetime
import openerp.netsvc as netsvc


class report_commission_wizard(osv.osv_memory):
    _name = 'report.commission.wizard'
    _description = u'Wizard de Relatório de comissão'

    _columns = {
        'start_date': fields.date('Data de Inicio', required=True),
        'end_date': fields.date('Data Final', required=True),
        'result': fields.binary('Resultado', readonly=True)
    }

    _defaults = {
        'start_date': lambda s, c, u, ctx: datetime.now().replace(day=1).
        strftime('%Y-%m-%d'),
        'end_date': lambda s, c, u, ctx: datetime.now().strftime('%Y-%m-%d'),
    }

    def action_generate_report(self, cr, uid, ids, context=None):
        items = self.browse(cr, uid, ids, context=context)

        inicio = datetime.strptime(items[0].start_date, '%Y-%m-%d')
        final = datetime.strptime(items[0].end_date, '%Y-%m-%d')

        sql = "select distinct(partner_id) from \
        contract_partner_commission_report where date between %s and %s"
        cr.execute(sql, (inicio, final))
        partners = cr.fetchall()
        ids = [x[0] for x in partners]

        datas = {
             'model': 'res.partner',
             'start_date': items[0].start_date,
             'end_date': items[0].end_date,
             'formatted_start_date': inicio.strftime("%d/%m/%Y"),
             'formatted_end_date': final.strftime("%d/%m/%Y"),
        }

        obj = netsvc.LocalService('report.commission.report')
        caminho = '/tmp/innova-pdf'
        if os.path.exists(caminho):
            shutil.rmtree(caminho)
        os.makedirs(caminho)

        for partner in ids:
            partner_obj = self.pool['res.partner'].browse(
                cr, uid, partner, context)
            (result, format) = obj.create(cr, uid, [partner], datas, context)
            name = partner_obj.legal_name or partner_obj.name
            path = os.path.join(caminho, '%s.pdf' % name.replace('/', ''))
            f = open(path, 'wb')
            f.write(result)
            f.close()

        def zipdir(path, ziph):
            # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    ziph.write(os.path.join(root, file), file)

        zipf = zipfile.ZipFile('/tmp/innova-pdf.zip', 'w',
                               zipfile.ZIP_DEFLATED)
        zipdir('/tmp/innova-pdf', zipf)
        zipf.close()

        zip_file = open('/tmp/innova-pdf.zip', 'rb').read()
        os.remove('/tmp/innova-pdf.zip')

        vals = {
            'start_date': items[0].start_date,
            'end_date': items[0].end_date,
            'result': base64.b64encode(zip_file)
        }
        id_wizard = self.create(cr, uid, vals, context)

        return {
            'type': 'ir.actions.act_window',
            'name': u'Relatório de Comissões',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': id_wizard,
            'res_model': 'report.commission.wizard',
            'nodestroy': True,
        }


report_commission_wizard()
