# Embedded file name: /opt/openerp/homolog/addons-extra/electronic_invoice/res_company.py
from osv import fields, osv
EI_SERVICE_VERSION = [('05030_1', 'S\xc3\xa3o Paulo/SP - 1'), ('110', 'Piracicaba/SP - 1.10')]
EI_PRODUCT_VERSION = [('310', '3.10')]
EI_ENVIRONMENT = [('test', 'Test'), ('production', 'Production')]
EI_TIPO_TRIBUTACAO = [('T', 'Tributado no municipio'),
 ('F', 'Tributado fora do municipio'),
 ('A', 'Tributado no municipio, porem Isento'),
 ('B', 'Tributado fora do municipio, porem Isento'),
 ('M', 'Tributado no municipio, porem Imune'),
 ('N', 'Tributado fora do municipio, porem Imune'),
 ('X', 'Tributado no municipio, porem Eligibilidade Suspensa'),
 ('V', 'Tributado fora do municipio, porem Eligibilidade Suspensa'),
 ('P', 'Exporta\xc3\xa7ao de Servi\xc3\xa7os')]

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {'tributacao': fields.selection(EI_TIPO_TRIBUTACAO, 'Tributa\xc3\xa7\xc3\xa3o'),
     'ei_service_version': fields.selection(EI_SERVICE_VERSION, 'Service Version'),
     'ei_product_version': fields.selection(EI_PRODUCT_VERSION, 'Product Version'),
     'ei_environment': fields.selection(EI_ENVIRONMENT, 'Environment'),
     'ei_service_description': fields.text('Service Description'),
     'accounting_responsible': fields.many2one('res.partner', 'Accounting Responsible', domain="[('supplier', '=', True)]")}
    _defaults = {'tributacao': 'T'}


res_company()