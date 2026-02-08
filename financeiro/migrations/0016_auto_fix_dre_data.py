from django.db import migrations
from django.db.models import Q

def fix_dre_production_data(apps, schema_editor):
    CategoriaFinanceira = apps.get_model('financeiro', 'CategoriaFinanceira')
    AccountReceivable = apps.get_model('financeiro', 'AccountReceivable')
    FinancialTransaction = apps.get_model('financeiro', 'FinancialTransaction')
    InvoiceItem = apps.get_model('faturamento', 'InvoiceItem')

    # 1. Obter a categoria principal de receita
    categoria_servico = CategoriaFinanceira.objects.filter(nome='Prestação de Serviços').first()
    if not categoria_servico:
        # Se não achar por nome exato (pode ter mudado no seed), tenta achar por grupo
        categoria_servico = CategoriaFinanceira.objects.filter(grupo_dre='Receita Operacional Bruta').first()
    
    if not categoria_servico:
        return

    # 2. Corrigir Itens de Fatura
    InvoiceItem.objects.filter(financial_category__isnull=True).update(financial_category=categoria_servico)

    # 3. Corrigir Contas a Receber
    receivables = AccountReceivable.objects.filter(category__isnull=True)
    for rec in receivables:
        rec.category = categoria_servico
        rec.save()

    # 4. Corrigir Transações Financeiras
    # Categoriza transações que pareçam ser de faturas ou recebimentos
    FinancialTransaction.objects.filter(
        Q(description__icontains='Fatura') | 
        Q(description__icontains='PAGAMENTO') |
        Q(description__icontains='PIX') |
        Q(description__icontains='Recebimento'),
        category__isnull=True
    ).update(category=categoria_servico)

class Migration(migrations.Migration):
    dependencies = [
        ('financeiro', '0015_seed_dre_data'),
        ('faturamento', '0011_invoiceitem_financial_category'),
        ('comercial', '0012_contractitem_financial_category'),
    ]

    operations = [
        migrations.RunPython(fix_dre_production_data),
    ]
