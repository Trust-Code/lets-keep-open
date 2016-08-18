# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name'        : 'Brazilian Contracts Management Extension',
    'version'     : '002.12',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Account',
    'summary'     : 'Extension of Contract Management Module',
    'description' : """

Improvements for Contract Management Module:
   * Create recurring invoices
   * Include especial conditions on create invoice
   * Groupping invoices on parent contract
   * Include equipaments (serial number) on contract
   * Sales Commission

""",
    'depends'     : ['account_analytic_analysis',
                     'hr_timesheet',
                     'stock'],
    'data'        : ['wizard/account_make_invoice.xml',
                     'wizard/account_renewal_view.xml',
                     'report/contract_commission_report_view.xml',
                     'account_analytic_analysis_view.xml',
                     'stock_view.xml'],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': True,
    'application' : False,
}
