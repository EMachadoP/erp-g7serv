from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceOrder, ServiceOrderItem
from financeiro.models import AccountReceivable, FinancialCategory
from estoque.models import StockMovement
from django.utils import timezone
from django.db.models.signals import pre_save

@receiver(post_save, sender=ServiceOrder)
def create_receivable_on_complete(sender, instance, created, **kwargs):
    """
    Creates an AccountReceivable when a ServiceOrder is marked as COMPLETED.
    """
    if instance.status == 'COMPLETED':
        # Check if a receivable already exists for this OS to avoid duplicates
        # We can use the description or a specific field if we added one.
        # For now, we'll check if there's a receivable with the description containing the OS ID.
        description = f"Ref. OS #{instance.id}"
        
        # Avoid creating duplicate if signal fires multiple times
        if not AccountReceivable.objects.filter(description=description).exists():
            
            # Try to find a default category for Services/Sales
            category = FinancialCategory.objects.filter(type='REVENUE').first()
            
            AccountReceivable.objects.create(
                description=description,
                client=instance.client,
                amount=instance.value,
                due_date=timezone.now().date(), # Default to today
                status='PENDING',
                category=category,
                occurrence_date=timezone.now().date()
            )

@receiver(pre_save, sender=ServiceOrder)
def check_status_change(sender, instance, **kwargs):
    """
    Checks if status is changing to COMPLETED to trigger stock deduction.
    We use pre_save to compare with old status, but actual deduction 
    should ideally happen after save to ensure consistency.
    However, for simplicity in this refactor, we'll do it in post_save 
    by checking a flag or just checking if it IS completed and wasn't before.
    
    Since we can't easily access 'old' in post_save without a query in pre_save,
    let's do a simple check: if it is COMPLETED, we check if stock movements 
    already exist for this OS completion.
    """
    pass

@receiver(post_save, sender=ServiceOrder)
def deduct_stock_on_complete(sender, instance, created, **kwargs):
    if instance.status == 'COMPLETED':
        # Check if we already deducted stock for this OS to avoid double deduction
        # We look for a StockMovement with reason containing the OS ID
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
