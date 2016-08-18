# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv, orm

class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        if context is None:
            context = {}
        if context.get('origin') == 'account.chart':
            account_chart_obj = self.pool.get('account.chart')
            last_id = 0
            for account_chart_id in account_chart_obj.search(cr, uid, [(1, '=', 1)]):
                if account_chart_id > last_id:
                    last_id = account_chart_id

            account_chart_rec = account_chart_obj.read(
                cr, uid, [last_id], [], context=context)[0]
            if account_chart_rec['target_move'] == 'posted':
                args.append(('move_id.state', '=', account_chart_rec['target_move']))
            if account_chart_rec['period_from'][0] and account_chart_rec['period_to'][0]:
                period_ids = self.pool.get('account.period').build_ctx_periods(cr, uid, account_chart_rec['period_from'][0], account_chart_rec['period_to'][0])
                args.append(('period_id', 'in', period_ids))
            elif account_chart_rec['fiscalyear'][0]:
                period_ids = self.pool.get('account.fiscalyear').browse(cr, uid, account_chart_rec['fiscalyear'][0], context=context).period_ids
                args.append(('period_id', 'in', period_ids))
        return super(account_move_line, self).search(cr, uid, args, offset, limit, order, context, count)

    def create_analytic_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ret = super(account_move_line, self).create_analytic_lines(
            cr, uid, ids, context=context)
        analytic_line_obj = self.pool.get('account.analytic.line')
        for move_line_rec in self.browse(cr, uid, ids, context=context):
            analytic_line_src = analytic_line_obj.search(
                cr, uid, [('move_id', '=', move_line_rec.id)])
            for analytic_line_rec in analytic_line_obj.browse(cr, uid, analytic_line_src, context=context):
                if not analytic_line_rec.move_id.analytic_account_id:
                    analytic_line_obj.unlink(cr, uid, analytic_line_rec.id, context=context)

        return ret


account_move_line()
