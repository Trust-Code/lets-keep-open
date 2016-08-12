# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_account_analytic_analysis_ext/wizard/account_renewal.py
from openerp.osv import fields, osv
import datetime
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

class account_renewal(osv.osv_memory):
    _name = 'account.renewal'
    _description = 'Account Renewal Contract'

    def make_renewal_contract(self, cr, uid, ids, context = None):

        def format_message(message_description, tracked_values):
            message = ''
            if message_description:
                message = '<span>%s</span>' % message_description
            for name, change in tracked_values.items():
                message += '<div> &nbsp; &nbsp; &bull; <b>%s</b>: ' % change.get('col_info')
                if change.get('old_value'):
                    message += '%s &rarr; ' % change.get('old_value')
                message += '%s</div>' % change.get('new_value')

            return message

        obj_account_analytic_account = self.pool.get('account.analytic.account')
        obj_recurring_invoice_line = self.pool.get('account.analytic.invoice.line')
        for rec_account_analytic_account in obj_account_analytic_account.browse(cr, uid, context.get('active_ids'), context=context):
            w_date = datetime.datetime.strptime(rec_account_analytic_account.date, '%Y-%m-%d')
            w_date_start_str = w_date - relativedelta(months=+rec_account_analytic_account.months_renewal)
            w_date_start = w_date_start_str.strftime('%Y-%m-%d')
            w_date_new_str = w_date + relativedelta(months=+rec_account_analytic_account.months_renewal)
            w_date_new = w_date_new_str.strftime('%Y-%m-%d')
            field_get = obj_account_analytic_account.fields_get(cr, uid, ['date'], context=context)
            tracked_values = {'date': {'new_value': w_date_new,
                      'old_value': rec_account_analytic_account.date,
                      'col_info': field_get['date']['string']}}
            for rec_recurring_invoice_line in rec_account_analytic_account.recurring_invoice_line_ids:
                w_rate = 0
                for rec_rate in rec_account_analytic_account.res_currency_id.rate_ids:
                    if rec_rate.name >= w_date_start and rec_rate.name <= rec_account_analytic_account.date:
                        w_rate += rec_rate.rate

                w_price_unit = round(rec_recurring_invoice_line.price_unit * (1 + w_rate / 100), 2)
                field_get = obj_recurring_invoice_line.fields_get(cr, uid, ['price_unit'], context=context)
                tracked_values['line' + str(rec_recurring_invoice_line.id)] = {'new_value': w_price_unit,
                 'old_value': rec_recurring_invoice_line.price_unit,
                 'col_info': field_get['price_unit']['string'] + ' - ' + rec_recurring_invoice_line.product_id.default_code}
                obj_recurring_invoice_line.write(cr, uid, [rec_recurring_invoice_line.id], {'price_unit': w_price_unit}, context=context)

            obj_account_analytic_account.write(cr, uid, [rec_account_analytic_account.id], {'date': w_date_new}, context=context)
            message = format_message(_('Contract Renewed') + ' - ' + rec_account_analytic_account.res_currency_id.name + ': ' + str(w_rate) + '%', tracked_values)
            obj_account_analytic_account.message_post(cr, uid, rec_account_analytic_account.id, body=message, context=context)


account_renewal()