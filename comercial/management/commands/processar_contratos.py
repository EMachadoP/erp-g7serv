from django.core.management.base import BaseCommand
from django.utils import timezone
from comercial.models import Contract
from financeiro.models import AccountReceivable, FinancialCategory
from faturamento.models import Invoice
from django.db import transaction

class Command(BaseCommand):
    help = 'Processa contratos ativos e gera faturas recorrentes'

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f'Iniciando processamento de contratos para {today.strftime("%d/%m/%Y")}')

        # Filter active contracts
        contracts = Contract.objects.filter(status='Ativo')
        
        count = 0
        for contract in contracts:
            # Check if today is equal or greater than due_day
            if today.day >= contract.due_day:
                
                # Check for duplicates in current Month/Year
                description_pattern = f"Fatura Contrato #{contract.id} - {today.strftime('%m/%Y')}"
                
                if AccountReceivable.objects.filter(description=description_pattern).exists():
                    self.stdout.write(self.style.WARNING(f'Fatura já existe para Contrato #{contract.id}'))
                    continue

                try:
                    with transaction.atomic():
                        # Create AccountReceivable
                        category = FinancialCategory.objects.filter(type='REVENUE').first()
                        
                        receivable = AccountReceivable.objects.create(
                            description=description_pattern,
                            client=contract.client,
                            amount=contract.value,
                            due_date=today.replace(day=contract.due_day), # Set due date to specific day
                            status='PENDING',
                            category=category,
                            occurrence_date=today
                        )
                        
                        # Create Invoice (Faturamento)
                        Invoice.objects.create(
                            client=contract.client,
                            contract=contract,
                            billing_group=contract.billing_group,
                            status='PD', # 'PENDING' in model choices is 'PD'? Model says 'PD', 'PG', 'CN'. Code used 'PENDING'.
                            # Wait, previous code used 'PENDING'. Model choices are: ('PD', 'Pendente').
                            # So 'PENDING' is invalid. Must use 'PD'.
                            issue_date=today,
                            due_date=today.replace(day=contract.due_day),
                            amount=contract.value,
                            number=f"FAT-{contract.id}-{today.strftime('%Y%m')}",
                            competence_month=today.month,
                            competence_year=today.year
                        )
                        
                        count += 1
                        self.stdout.write(self.style.SUCCESS(f'Fatura gerada para Contrato #{contract.id}'))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao gerar fatura para Contrato #{contract.id}: {e}'))
            else:
                 self.stdout.write(f'Contrato #{contract.id} ainda não venceu (Dia {contract.due_day})')

        self.stdout.write(self.style.SUCCESS(f'Processo concluído. {count} faturas geradas.'))
