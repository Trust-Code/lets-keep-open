# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Relatório de Comissões',
    "license": "AGPL-3",
    'category': 'Account',
    'summary': 'Módulo de comissões',
    'description': "Relatório - Módulo de Comissões",
    'depends': [
        'account_analytic_analysis',
        'hr_timesheet',
        'stock',
        'l10n_br_account_analytic_analysis_ext',
        'report_webkit'
    ],
    'data': [
        'wizard/report_commission.xml',
        'report/commission_report.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'application': False,
}
