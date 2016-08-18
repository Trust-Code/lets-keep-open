# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from osv import fields, osv
EI_SERVICE_VERSION = [('05030_1', 'São Paulo/SP - 1'), ('110', 'Piracicaba/SP - 1.10')]
EI_PRODUCT_VERSION = [('310', '3.10')]
EI_ENVIRONMENT = [('test', 'Test'), ('production', 'Production')]
EI_TIPO_TRIBUTACAO = [
    ('T', 'Tributado no municipio'),
    ('F', 'Tributado fora do municipio'),
    ('A', 'Tributado no municipio, porem Isento'),
    ('B', 'Tributado fora do municipio, porem Isento'),
    ('M', 'Tributado no municipio, porem Imune'),
    ('N', 'Tributado fora do municipio, porem Imune'),
    ('X', 'Tributado no municipio, porem Eligibilidade Suspensa'),
    ('V', 'Tributado fora do municipio, porem Eligibilidade Suspensa'),
    ('P', 'Exportação de Serviços')]

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'tributacao': fields.selection(EI_TIPO_TRIBUTACAO, 'Tributação'),
        'ei_service_version': fields.selection(EI_SERVICE_VERSION, 'Service Version'),
        'ei_product_version': fields.selection(EI_PRODUCT_VERSION, 'Product Version'),
        'ei_environment': fields.selection(EI_ENVIRONMENT, 'Environment'),
        'ei_service_description': fields.text('Service Description'),
        'accounting_responsible': fields.many2one('res.partner', 'Accounting Responsible', domain="[('supplier', '=', True)]")
    }
    _defaults = {'tributacao': 'T'}


res_company()
