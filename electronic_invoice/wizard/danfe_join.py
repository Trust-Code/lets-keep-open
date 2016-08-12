# Embedded file name: /opt/openerp/homolog/addons-extra/electronic_invoice/wizard/danfe_join.py
from osv import osv, fields
from openerp.osv import fields, orm
from openerp.tools.translate import _
from datetime import datetime, date
from PyPDF2 import PdfFileReader, PdfFileWriter
from tempfile import mkstemp
from werkzeug.wrappers import Response
import base64
import pytz
import os

class danfe_join(osv.osv):
    _name = 'danfe.join'

    def danfe_join(self, cr, uid, ids, context = None):
        account_i_obj = self.pool.get('account.invoice').browse(cr, uid, context['active_ids'], context=context)
        output = PdfFileWriter()
        list_attachments = []
        for rec_account_invoice in account_i_obj:
            attach_pool = self.pool.get('ir.attachment')
            attach_ids = attach_pool.search(cr, uid, [('res_id', '=', rec_account_invoice.id), ('res_model', '=', 'account.invoice')])
            if attach_ids:
                for ir_attachment in attach_pool.browse(cr, uid, attach_ids, context=None):
                    if ir_attachment.name[-3:] == 'pdf':
                        list_attachments.append(ir_attachment)

        for ir_attachment_obj in list_attachments:
            fd, file_name = mkstemp()
            os.write(fd, base64.decodestring(attach_pool.browse(cr, uid, ir_attachment_obj.id).datas))
            pdf = PdfFileReader(file(file_name, 'rb'))
            pg_pdf = pdf.getNumPages()
            for i in range(0, pg_pdf):
                output.addPage(pdf.getPage(i))

            os.remove(os.path.join(file_name))

        if not list_attachments:
            raise orm.except_orm(_('Error'), 'The PDF file is empty, no exists attachments for join the file.')
        fd_fl, file_name_fl = mkstemp()
        outputStream = file(file_name_fl, 'w+b')
        output.write(outputStream)
        outputStream.seek(0)
        ps = outputStream.read()
        outputStream.close()
        w_file = base64.b64encode(ps)
        w_timezone = self.pool.get('res.users').browse(cr, uid, uid).tz
        now = datetime.now(pytz.timezone(w_timezone))
        filename = 'DANFE_UN_%04d-%02d-%02d.pdf' % (now.year, now.month, now.day)
        id_danfe_join = self.create(cr, uid, {'data': w_file,
         'filename': filename,
         'invisible': True}, context=context)
        os.remove(os.path.join(file_name_fl))
        return {'type': 'ir.actions.act_window',
         'res_model': 'danfe.join',
         'view_mode': 'form',
         'view_type': 'form',
         'res_id': id_danfe_join,
         'views': [(False, 'form')],
         'target': 'new'}

    _columns = {'filename': fields.char('Filename'),
     'data': fields.binary('File', readonly=True),
     'invisible': fields.boolean('Button Invisible')}