
MENU_PERMISSIONS = [
    {
        'name': 'Administrativo',
        'icon': 'bi-building',
        'submenus': [
            {'name': 'Pessoas', 'url': 'comercial:client_list', 'perm': 'core.view_person'},
            {'name': 'Serviços', 'url': 'comercial:service_list', 'perm': 'comercial.view_service'},
            {'name': 'Produtos', 'url': 'estoque:product_list', 'perm': 'estoque.view_product'},
            {'name': 'Marcas', 'url': 'estoque:brand_list', 'perm': 'estoque.view_brand'},
            {'name': 'Grupo de Produtos', 'url': 'estoque:category_list', 'perm': 'estoque.view_category'},
            {'name': 'Usuários', 'url': 'core:user_list', 'perm': 'auth.view_user'},
            {'name': 'Perfis', 'url': 'core:profile_list', 'perm': 'auth.view_group'},
        ]
    },
    {
        'name': 'Comercial',
        'icon': 'bi-briefcase',
        'submenus': [
            {'name': 'Orçamentos', 'url': 'comercial:budget_list', 'perm': 'comercial.view_budget'},
            {'name': 'Contratos', 'url': 'comercial:contract_list', 'perm': 'comercial.view_contract'},
            {'name': 'Ações de Vendas', 'url': 'comercial:sales_actions', 'perm': 'comercial.view_budget'},
        ]
    },
    {
        'name': 'Operacional',
        'icon': 'bi-tools',
        'submenus': [
            {'name': 'Andamento do Operacional', 'url': 'operacional:operational_progress', 'perm': 'operacional.view_serviceorder'}, # Using ServiceOrder for now
            {'name': 'Ordem de Serviço', 'url': 'operacional:service_order_list', 'perm': 'operacional.view_serviceorder'},
        ]
    },
    {
        'name': 'Faturamento',
        'icon': 'bi-cash-coin',
        'url': 'faturamento:list',
        'perm': 'comercial.view_contract', # Assuming billing is related to contracts for now
    },
    {
        'name': 'Financeiro',
        'icon': 'bi-currency-dollar',
        'submenus': [
            {'name': 'Visão Geral', 'url': 'reports:dashboard', 'perm': 'financeiro.view_accountpayable'}, # Using generic financial perm
            {'name': 'Contas a Pagar', 'url': 'financeiro:account_payable_list', 'perm': 'financeiro.view_accountpayable'},
            {'name': 'Contas a Receber', 'url': 'financeiro:account_receivable_list', 'perm': 'financeiro.view_accountreceivable'},
            {'name': 'Recibos', 'url': 'financeiro:receipt_list', 'perm': 'financeiro.view_receipt'},
            {'name': 'Planejamento Orçamentário', 'url': 'financeiro:budget_plan_list', 'perm': 'financeiro.view_budgetplan'},
        ]
    },
    {
        'name': 'Estoque',
        'icon': 'bi-box-seam',
        'url': 'estoque:product_list',
        'perm': 'estoque.view_product',
    },
    {
        'name': 'Relatórios',
        'icon': 'bi-printer',
        'url': 'reports:dashboard',
        'perm': 'auth.view_user', # Placeholder
    }
]
