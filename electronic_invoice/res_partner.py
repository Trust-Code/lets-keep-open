# Embedded file name: /opt/openerp/homolog/addons-extra/electronic_invoice/res_partner.py
from openerp.osv import orm, fields


class res_partner(orm.Model):
    _inherit = 'res.partner'
    _columns = {
        'ei_service_description': fields.text('EI Description')
    }
