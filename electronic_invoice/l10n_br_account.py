# Embedded file name: /opt/openerp/homolog/addons-extra/electronic_invoice/l10n_br_account.py
from openerp.osv import orm, fields


class l10n_br_account_service_type(orm.Model):
    _inherit = 'l10n_br_account.service.type'
    _columns = {
        'ei_description': fields.text('Electronic Invoice Description')
    }
