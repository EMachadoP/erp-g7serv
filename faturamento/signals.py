from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice
from financeiro.models import AccountReceivable, FinancialCategory
from decimal import Decimal

@receiver(post_save, sender=Invoice)
def create_account_receivable(sender, instance, created, **kwargs):
    """
    Sempre que uma Invoice (Fatura) for criada, cria automaticamente um registro 
    no Contas a Receber do financeiro.
    """
    if created:
        # Tenta obter ou criar uma categoria padrão para Receita de Faturas
        category, _ = FinancialCategory.objects.get_or_create(
            name="Receita de Faturas",
            defaults={'type': 'REVENUE'}
        )
        
        # Evita duplicidade se já existir um recebível para esta invoice
        if not AccountReceivable.objects.filter(invoice=instance).exists():
            description = f"Fatura #{instance.number}"
            if instance.client:
                description += f" - {instance.client.name}"
                
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
