from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceOrder, ServiceOrderItem
from financeiro.models import AccountReceivable, CategoriaFinanceira
from estoque.models import StockMovement
from django.utils import timezone
from django.db.models.signals import pre_save

@receiver(post_save, sender=ServiceOrder)
def create_receivable_on_complete(sender, instance, created, **kwargs):
    """
    Creates an AccountReceivable when a ServiceOrder is marked as COMPLETED.
    """
    if instance.status == 'COMPLETED':
        description = f"Ref. OS #{instance.id}"
        
        if not AccountReceivable.objects.filter(description=description).exists():
            
            # Try to find a default category for Services/Sales
            category = CategoriaFinanceira.objects.filter(tipo='entrada').first()
            
            AccountReceivable.objects.create(
                description=description,
                client=instance.client,
                amount=instance.value,
                due_date=timezone.now().date(),
                status='PENDING',
                category=category,
                occurrence_date=timezone.now().date()
            )

@receiver(pre_save, sender=ServiceOrder)
def check_status_change(sender, instance, **kwargs):
    pass

@receiver(post_save, sender=ServiceOrder)
def deduct_stock_on_complete(sender, instance, created, **kwargs):
    if instance.status == 'COMPLETED':
        reason_pattern = f"Ordem de Serviço #{instance.id} - Conclusão"
        
        if not StockMovement.objects.filter(reason=reason_pattern).exists():
            items = instance.items.all()
            for item in items:
                StockMovement.objects.create(
                    product=item.product,
                    movement_type='OUT',
                    quantity=item.quantity,
                    reason=reason_pattern
                )
