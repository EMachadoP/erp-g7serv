from django.core.management.base import BaseCommand
from financeiro.models import AccountReceivable, FinancialTransaction, CategoriaFinanceira
from faturamento.models import InvoiceItem, Invoice
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix existing financial data by assigning correct categories for DRE report.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando correção de dados para DRE...")
        
        # 1. Obter a categoria principal de receita
        categoria_servico = CategoriaFinanceira.objects.filter(nome='Prestação de Serviços').first()
        if not categoria_servico:
            self.stdout.write(self.style.ERROR("Erro: Categoria 'Prestação de Serviços' não encontrada. Execute a migração de seed primeiro."))
            return

        with transaction.atomic():
            # 2. Corrigir Itens de Fatura (InvoiceItem)
            # Todos os itens de fatura que não possuem categoria recebem 'Prestação de Serviços'
            items_to_fix = InvoiceItem.objects.filter(financial_category__isnull=True)
            count_items = items_to_fix.count()
            items_to_fix.update(financial_category=categoria_servico)
            self.stdout.write(f"- {count_items} itens de fatura categorizados.")

            # 3. Corrigir Contas a Receber (AccountReceivable)
            # Prioridade: Herdar da Fatura se houver, senão fallback para 'Prestação de Serviços'
            receivables = AccountReceivable.objects.filter(category__isnull=True)
            count_rec = 0
            for rec in receivables:
                if rec.invoice:
                    first_item = rec.invoice.items.first()
                    if first_item and first_item.financial_category:
                        rec.category = first_item.financial_category
                    else:
                        rec.category = categoria_servico
                else:
                    rec.category = categoria_servico
                rec.save()
                count_rec += 1
            self.stdout.write(f"- {count_rec} contas a receber categorizadas.")

            # 4. Corrigir Transações Financeiras (FinancialTransaction)
            # Transações sem categoria que vieram de faturas ou descrições similares
            transactions = FinancialTransaction.objects.filter(category__isnull=True)
            count_trans = 0
            for trans in transactions:
                if "Fatura" in trans.description or "PAGAMENTO PIX" in trans.description:
                    trans.category = categoria_servico
                    trans.save()
                    count_trans += 1
            self.stdout.write(f"- {count_trans} transações de caixa categorizadas.")

        self.stdout.write(self.style.SUCCESS("Correção concluída com sucesso!"))
