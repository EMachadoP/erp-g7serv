from django.core.management.base import BaseCommand
from financeiro.models import FinancialCategory

class Command(BaseCommand):
    help = 'Popula as categorias financeiras para estrutura de DRE'

    def handle(self, *args, **options):
        # Estrutura: (Nome, Tipo, Pai_None, Subcategorias_List)
        structure = [
            ('1. Receitas', 'REVENUE', [
                ('1.1 Receita de Serviços', 'REVENUE', [
                    ('Instalação/implantação', 'REVENUE'),
                    ('Manutenção corretiva avulsa', 'REVENUE'),
                    ('Visita técnica/diagnóstico', 'REVENUE'),
                    ('Outros serviços', 'REVENUE'),
                ]),
                ('1.2 Receita de Vendas', 'REVENUE', [
                    ('Venda de equipamentos', 'REVENUE'),
                    ('Venda de peças/consumíveis', 'REVENUE'),
                    ('Frete cobrado do cliente', 'REVENUE'),
                ]),
                ('1.3 Receita de Contratos', 'REVENUE', [
                    ('Mensalidade de contratos', 'REVENUE'),
                    ('Extras de contrato', 'REVENUE'),
                ]),
            ]),
            ('2. Deduções da Receita', 'EXPENSE', [
                ('Simples Nacional – DAS', 'EXPENSE'),
                ('Descontos concedidos', 'EXPENSE'),
                ('Estornos / Cancelamentos', 'EXPENSE'),
                ('Taxas de cartão', 'EXPENSE'),
            ]),
            ('3. Custos Diretos (CMV)', 'EXPENSE', [
                ('3.1 Custos diretos de Serviços e Contratos', 'EXPENSE', [
                    ('Mão de obra técnica', 'EXPENSE'),
                    ('Terceiros / prestadores', 'EXPENSE'),
                    ('Materiais aplicados em serviço', 'EXPENSE'),
                    ('Deslocamento de atendimento', 'EXPENSE'),
                ]),
                ('3.2 CMV – Custo de Produtos Vendidos', 'EXPENSE', [
                    ('Custo do produto vendido', 'EXPENSE'),
                    ('Frete de compra', 'EXPENSE'),
                    ('Perdas/avarias/garantia', 'EXPENSE'),
                ]),
            ]),
            ('4. Despesas Operacionais (OPEX)', 'EXPENSE', [
                ('4.1 Comercial', 'EXPENSE', [
                    ('Comissões', 'EXPENSE'),
                    ('Marketing / anúncios', 'EXPENSE'),
                    ('Ferramentas comerciais', 'EXPENSE'),
                ]),
                ('4.2 Administrativas', 'EXPENSE', [
                    ('Salários administrativos', 'EXPENSE'),
                    ('Pró-labore', 'EXPENSE'),
                    ('Contabilidade', 'EXPENSE'),
                    ('Aluguel + despesas da sede', 'EXPENSE'),
                    ('Materiais de escritório', 'EXPENSE'),
                ]),
                ('4.3 Operacionais (estrutura)', 'EXPENSE', [
                    ('Sistemas e assinaturas', 'EXPENSE'),
                    ('Manutenção de veículos', 'EXPENSE'),
                    ('Ferramentas / EPI / uniformes', 'EXPENSE'),
                ]),
            ]),
            ('5. Resultado Financeiro', 'EXPENSE', [
                ('Tarifas bancárias', 'EXPENSE'),
                ('Juros pagos', 'EXPENSE'),
                ('Juros/multas recebidos', 'REVENUE'),
            ]),
            ('6. Depreciação', 'EXPENSE', [
                ('Depreciação de veículos', 'EXPENSE'),
                ('Depreciação de equipamentos', 'EXPENSE'),
            ]),
            ('7. Não Operacional', 'EXPENSE', [
                ('Multas/contingências', 'EXPENSE'),
                ('Venda de ativo', 'REVENUE'),
            ]),
        ]

        def create_recursive(items, parent=None):
            for item in items:
                name = item[0]
                type_code = item[1]
                subs = item[2] if len(item) > 2 else []
                
                cat, created = FinancialCategory.objects.get_or_create(
                    name=name,
                    parent=parent,
                    defaults={'type': type_code}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Criada: {name}'))
                
                if isinstance(subs, list):
                    create_recursive(subs, cat)

        create_recursive(structure)
        self.stdout.write(self.style.SUCCESS('Seeding concluído com sucesso!'))
