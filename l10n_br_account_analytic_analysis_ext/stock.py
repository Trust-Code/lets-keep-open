# Embedded file name: /opt/openerp/homolog/addons-extension/l10n_br_account_analytic_analysis_ext/stock.py
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class stock_production_lot(osv.osv):
    _name = 'stock.production.lot'
    _inherit = 'stock.production.lot'
    _columns = {'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account')}


stock_production_lot()