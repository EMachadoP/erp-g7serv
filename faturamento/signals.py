from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Invoice, InvoiceItem
from financeiro.models import AccountReceivable, FinancialCategory
from django.db.models import Sum
from decimal import Decimal

@receiver(post_save, sender=Invoice)
def sync_account_receivable(sender, instance, created, **kwargs):
    """
    Sincroniza o Contas a Receber sempre que a Fatura for salva.
    Cria se não existir, atualiza se já existir.
    """
    category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Faturas",
        defaults={'type': 'REVENUE'}
    )
    
    receivable = AccountReceivable.objects.filter(invoice=instance).first()
    
    description = f"Fatura #{instance.number}"
    if instance.client:
        description += f" - {instance.client.name}"

    if not receivable:
        # Criar se não existir
        AccountReceivable.objects.create(
            description=description,
            client=instance.client,
            category=category,
            amount=instance.amount,
            due_date=instance.due_date,
            status='PENDING',
            invoice=instance,
            document_number=instance.number
        )
    else:
        # Atualizar se já existir (valor e vencimento)
        receivable.amount = instance.amount
        receivable.due_date = instance.due_date
        receivable.description = description
        receivable.save()

@receiver([post_save, post_delete], sender=InvoiceItem)
def update_invoice_amount(sender, instance, **kwargs):
    """
    Atualiza o valor total da Fatura (Invoice.amount) sempre que um item for
    adicionado, alterado ou removido.
    """
    invoice = instance.invoice
    total = invoice.items.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Só atualiza se o valor for diferente para evitar loops de sinais
    if invoice.amount != total:
        invoice.amount = total
        invoice.save()
