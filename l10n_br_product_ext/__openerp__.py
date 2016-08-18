# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name'        : 'Brazilian Products & Pricelists Extension',
    'version'     : '001.02',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Sales Management',
    'sequence'    : 16,
    'summary'     : 'Extension of Products & Pricelists Module',
    'description' : """

Improvements for Products & Pricelists Module:
    * Discount Invoice Price.

""",
    'depends'     : ['l10n_br_product'],
    'data'        : ['pricelist_view.xml'],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': False,
    'application' : False,
}
