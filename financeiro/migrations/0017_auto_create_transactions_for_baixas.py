from django.db import migrations
from django.utils import timezone

def create_missing_transactions(apps, schema_editor):
    AccountReceivable = apps.get_model('financeiro', 'AccountReceivable')
    AccountPayable = apps.get_model('financeiro', 'AccountPayable')
    FinancialTransaction = apps.get_model('financeiro', 'FinancialTransaction')
    CashAccount = apps.get_model('financeiro', 'CashAccount')
    
    default_account = CashAccount.objects.first()
    if not default_account:
        return

    # 1. Recebíveis (Entradas)
    receivables = AccountReceivable.objects.filter(status='RECEIVED')
    for rec in receivables:
        # Verifica se já existe transação
        exists = FinancialTransaction.objects.filter(related_receivable=rec).exists()
        if not exists:
            # Cria transação faltante
            FinancialTransaction.objects.create(
                description=f"Recebimento {rec.description}",
                amount=rec.amount,
                transaction_type='IN',
                date=rec.receipt_date or timezone.now().date(),
                account=rec.account or default_account,
                category=rec.category,
                related_receivable=rec
            )

    # 2. Pagáveis (Saídas)
    # Pela minha análise, o 'realizar_baixa_conta' já cria transação,
    # mas alguns registros podem ter sido criados via sync ou manualmente sem passar pela view.
    payables = AccountPayable.objects.filter(status='PAID')
    for pay in payables:
        exists = FinancialTransaction.objects.filter(related_payable=pay).exists()
        if not exists:
            FinancialTransaction.objects.create(
                description=f"Pagamento {pay.description}",
                amount=pay.amount,
                transaction_type='OUT',
                date=pay.payment_date or timezone.now().date(),
                account=pay.account or default_account,
                category=pay.category,
                related_payable=pay
            )

def reverse_transactions(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('financeiro', '0016_auto_fix_dre_data'),
    ]

    operations = [
        migrations.RunPython(create_missing_transactions, reverse_transactions),
    ]
