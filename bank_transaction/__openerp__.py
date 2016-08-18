# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name'        : 'Brazilian Bank Transaction',
    'version'     : '001.11',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Accounting',
    'sequence'    : 38,
    'summary'     : 'Export and Import Bank Transactions for Brasilian Banks',
    'description' : '''
Generate CNAB files to send the bank and import CNAB files to update system
''',
    'depends'     : ['l10n_br_account',
                     'l10n_br_base',
                     'account_payment_extension'],
    'data'        : ['account_payment_extension_view.xml',
                     'sequence_type.xml',
                     'sequences.xml',
                     'menu_cnab.xml',
                     'file_format_view.xml',
                     'res_partner_view.xml',
                     'res_bank_view.xml',
                     'wizard/file_format_loader_view.xml',
                     'wizard/export_cnab_view.xml',
                     'wizard/import_cnab_view.xml',
                     'edi/payment_slip_email_template.xml',
                     'payment_slip_view.xml',
                     'bank_file.xml'],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': True,
    'application' : False,
}
