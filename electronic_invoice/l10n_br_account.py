# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class l10n_br_account_service_type(orm.Model):
    _inherit = 'l10n_br_account.service.type'
    _columns = {
        'ei_description': fields.text('Electronic Invoice Description')
    }
