# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.osv import orm, fields
import datetime

class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _columns = {
        'rps_code': fields.char('RPS Code', readonly=True, track_visibility='onchange'),
        'rps_serie': fields.char('RPS Serie', readonly=True, track_visibility='onchange'),
        'ei_status': fields.selection([('inactive', 'Inactive'),
                   ('scheduled', 'Scheduled'),
                   ('failed', 'Failed'),
                   ('cancelled', 'Cancelled'),
                   ('sent', 'Sent'),
                   ('confirmed', 'Confirmed')], 'EI Status', readonly=True, track_visibility='onchange'),
        'ei_date': fields.date('EI Date', readonly=True, track_visibility='onchange'),
        'ei_code': fields.char('EI Code', readonly=True, track_visibility='onchange'),
        'ei_verification_code': fields.char('EI Verification Code', readonly=True, track_visibility='onchange'),
        'ei_access_key': fields.char('EI Access Key', readonly=True),
        'ei_protocol': fields.char('EI Protocol', readonly=True),
        'ei_description': fields.text('EI Description'),
        'ei_events_ids': fields.one2many('electronic.invoice.event', 'invoice_id', 'Electronic Invoice Event', readonly=True),
        'ei_justification': fields.text('EI Justification'),
        'ei_correction_letter': fields.text('EI Correction Letter')}

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'rps_code': False,
            'rps_serie': False,
            'ei_status': False,
            'ei_date': False,
            'ei_code': False,
            'ei_verification_code': False,
            'ei_access_key': False,
            'ei_protocol': False,
            'ei_description': False,
            'ei_events_ids': False})
        return super(account_invoice, self).copy(cr, uid, id, default, context)

    def invoice_validate(self, cr, uid, ids, context=None):
        for br_account_invoice in self.browse(cr, uid, ids):
            if br_account_invoice.fiscal_type == 'service':
                self.write(cr, uid, ids, {'rps_code': self.pool.get('ir.sequence').get(cr, uid, 'rps.code.seq')}, context=context)

        return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)

    def action_cancel_draft(self, cr, uid, ids, *args):
        nfe_dict = {
            'rps_code': False,
            'rps_serie': False,
            'ei_status': False,
            'ei_date': False,
            'ei_code': False,
            'ei_verification_code': False,
            'ei_access_key': False,
            'ei_protocol': False,
            'ei_description': False,
            'ei_events_ids': False}
        self.write(cr, uid, ids, nfe_dict)
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, *args)


account_invoice()

class electronic_invoice_event(orm.Model):
    _name = 'electronic.invoice.event'
    _columns = {
        'event_date': fields.datetime('Event Date', readonly=True),
        'user_id': fields.many2one('res.users', 'User', readonly=True),
        'action': fields.selection([
            ('send', 'Send'),
            ('cancel', 'Cancel'),
            ('check', 'Check'),
            ('inactivate', 'Inactivate'),
            ('correction_letter', 'Correction Letter')], 'Action', readonly=True),
        'message': fields.char('Message', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True)
    }

    def create(self, cr, uid, vals, context=None):
        vals['event_date'] = vals.get('event_date') or datetime.datetime.now()
        vals['user_id'] = vals.get('user_id') or uid
        return super(electronic_invoice_event, self).create(cr, uid, vals, context=context)


electronic_invoice_event()
