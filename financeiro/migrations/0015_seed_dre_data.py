from django.db import migrations

def seed_data(apps, schema_editor):
    CentroResultado = apps.get_model('financeiro', 'CentroResultado')
    CategoriaFinanceira = apps.get_model('financeiro', 'CategoriaFinanceira')

    # 1. Centros de Resultado
    centros = [
        {'nome': 'Operacional', 'code': 'OP'},
        {'nome': 'Administrativo', 'code': 'ADM'},
        {'nome': 'Comercial', 'code': 'COM'},
    ]
    
    for c_data in centros:
        CentroResultado.objects.get_or_create(
            code=c_data['code'],
            defaults={'nome': c_data['nome']}
        )

    # 2. Categorias Financeiras (Entradas)
    entradas = [
        {'nome': 'Vendas de Produtos', 'grupo_dre': 'Receita Operacional Bruta', 'ordem': 10},
        {'nome': 'Prestação de Serviços', 'grupo_dre': 'Receita Operacional Bruta', 'ordem': 20},
        {'nome': 'Receitas Financeiras', 'grupo_dre': 'Resultado Financeiro', 'ordem': 100},
        {'nome': 'Outras Receitas', 'grupo_dre': 'Receitas Não Operacionais', 'ordem': 110},
    ]

    for cat in entradas:
        CategoriaFinanceira.objects.get_or_create(
            nome=cat['nome'],
            tipo='entrada',
            defaults={
                'grupo_dre': cat['grupo_dre'],
                'ordem_exibicao': cat['ordem']
            }
        )

    # 3. Categorias Financeiras (Saídas)
    saidas = [
        {'nome': 'Impostos sobre Vendas', 'grupo_dre': 'Deduções da Receita Bruta', 'ordem': 30},
        {'nome': 'Custo de Produtos Vendidos (CPV)', 'grupo_dre': 'Custos (CPV/CSP)', 'ordem': 40},
        {'nome': 'Custo de Serviços Prestados (CSP)', 'grupo_dre': 'Custos (CPV/CSP)', 'ordem': 50},
        {'nome': 'Salários e Proventos', 'grupo_dre': 'Despesas com Pessoal', 'ordem': 60},
        {'nome': 'Encargos Sociais', 'grupo_dre': 'Despesas com Pessoal', 'ordem': 70},
        {'nome': 'Aluguel / Condomínio', 'grupo_dre': 'Despesas Administrativas', 'ordem': 80},
        {'nome': 'Energia / Água / Internet', 'grupo_dre': 'Despesas Administrativas', 'ordem': 90},
        {'nome': 'Material de Escritório', 'grupo_dre': 'Despesas Administrativas', 'ordem': 100},
        {'nome': 'Marketing e Publicidade', 'grupo_dre': 'Despesas Comerciais', 'ordem': 110},
        {'nome': 'Comissões de Vendas', 'grupo_dre': 'Despesas Comerciais', 'ordem': 120},
        {'nome': 'Tarifas Bancárias', 'grupo_dre': 'Resultado Financeiro', 'ordem': 130},
        {'nome': 'Juros e Multas Pagos', 'grupo_dre': 'Resultado Financeiro', 'ordem': 140},
    ]

    for cat in saidas:
        CategoriaFinanceira.objects.get_or_create(
            nome=cat['nome'],
            tipo='saida',
            defaults={
                'grupo_dre': cat['grupo_dre'],
                'ordem_exibicao': cat['ordem']
            }
        )

def reverse_seed(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0014_centroresultado_categoriafinanceira_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_seed),
    ]
