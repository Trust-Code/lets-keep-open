# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name'        : 'Brazilian Sale Extension',
    'version'     : '1.0',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Sale',
    'summary'     : 'Extension of Sale Module',
    'description' : """

Improvements for Sale Module:
    * Change Account when create Invoice for Multi-Company
    * Change Fiscal Category when Shop is changed
    * Blocked Unit Price Input
    * Bug Fix when payment in Sales Order

""",
    'depends'     : ['l10n_br_sale',
                     'l10n_br_delivery'],
    'data'        : ['security/sale_security.xml',
                     'sale_report.xml',
                     'sale_view.xml'],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': True,
    'application' : False,
}
