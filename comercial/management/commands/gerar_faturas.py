from django.core.management.base import BaseCommand
from django.utils import timezone
from comercial.models import Contract
from financeiro.models import AccountReceivable, CategoriaFinanceira
from faturamento.models import Invoice
from django.db import transaction

class Command(BaseCommand):
    help = 'Gera faturas recorrentes para contratos ativos'

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f'Iniciando geração de faturas para {today.strftime("%d/%m/%Y")}')

        # Filter active contracts
        contracts = Contract.objects.filter(status='Ativo')
        
        count = 0
        for contract in contracts:
            # We can use a description pattern to check existence
            description_pattern = f"Fatura Contrato #{contract.id} - {today.strftime('%m/%Y')}"
            
            if AccountReceivable.objects.filter(description=description_pattern).exists():
                self.stdout.write(self.style.WARNING(f'Fatura já existe para Contrato #{contract.id}'))
                continue

            # Check if today is the due day
            if today.day != contract.due_day:
                 import calendar
                 last_day = calendar.monthrange(today.year, today.month)[1]
                 if not (today.day == last_day and contract.due_day >= last_day):
                     if today.day != contract.due_day:
                        continue

            try:
                with transaction.atomic():
                    # Create AccountReceivable
                    category = CategoriaFinanceira.objects.filter(tipo='entrada').first()
                    
                    receivable = AccountReceivable.objects.create(
                        description=description_pattern,
                        client=contract.client,
                        amount=contract.value,
                        due_date=today,
                        status='PENDING',
                        category=category,
                        occurrence_date=today
                    )
                    
                    # Create Invoice (Faturamento)
                    Invoice.objects.create(
                        client=contract.client,
                        contract=contract,
                        billing_group=contract.billing_group,
                        status='PD', # Changed from 'PENDING' to 'PD'
                        issue_date=today,
                        due_date=today,
                        amount=contract.value,
                        number=f"FAT-{contract.id}-{today.strftime('%Y%m')}",
                        competence_month=today.month,
                        competence_year=today.year
                    )
                    
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f'Fatura gerada para Contrato #{contract.id}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao gerar fatura para Contrato #{contract.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Processo concluído. {count} faturas geradas.'))
