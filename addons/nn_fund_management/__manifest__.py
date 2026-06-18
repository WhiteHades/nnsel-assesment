{
    'name': 'NN Fund Management',
    'version': '1.0',
    'category': 'Accounting/Fund Management',
    'summary': 'Manage incoming funds, allocations, requisitions, bills, transfers, and approvals',
    'author': 'Efaz',
    'depends': [
        'mail',
        'project',
    ],
    'data': [
        'security/nn_fund_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/approval_rule_data.xml',
        'data/demo_data.xml',
        'views/fund_account_views.xml',
        'views/fund_request_views.xml',
        'views/fund_config_views.xml',
        'views/fund_dashboard_views.xml',
        'views/fund_menus.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'nn_fund_management/static/src/scss/nn_fund_management.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
