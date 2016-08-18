# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class res_partner(orm.Model):
    _inherit = 'res.partner'
    _columns = {
        'ei_service_description': fields.text('EI Description')
    }
