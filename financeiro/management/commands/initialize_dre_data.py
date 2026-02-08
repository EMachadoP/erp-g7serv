from django.core.management.base import BaseCommand
from financeiro.models import CategoriaFinanceira, CentroResultado

class Command(BaseCommand):
    help = 'Inicializa categorias financeiras e centros de resultado para suporte à DRE'

    def handle(self, *args, **options):
        # 1. Centros de Resultado
        centros = [
            {'nome': 'Operacional', 'code': 'OP'},
            {'nome': 'Administrativo', 'code': 'ADM'},
            {'nome': 'Comercial', 'code': 'COM'},
        ]
        
        for c_data in centros:
            obj, created = CentroResultado.objects.get_or_create(
                code=c_data['code'],
                defaults={'nome': c_data['nome']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Centro de Resultado "{obj.nome}" criado.'))

        # 2. Categorias Financeiras (Entradas)
        entradas = [
            {'nome': 'Vendas de Produtos', 'grupo_dre': 'Receita Operacional Bruta', 'ordem': 10},
            {'nome': 'Prestação de Serviços', 'grupo_dre': 'Receita Operacional Bruta', 'ordem': 20},
            {'nome': 'Receitas Financeiras', 'grupo_dre': 'Resultado Financeiro', 'ordem': 100},
            {'nome': 'Outras Receitas', 'grupo_dre': 'Receitas Não Operacionais', 'ordem': 110},
        ]

        for cat in entradas:
            obj, created = CategoriaFinanceira.objects.get_or_create(
                nome=cat['nome'],
                tipo='entrada',
                defaults={
                    'grupo_dre': cat['grupo_dre'],
                    'ordem_exibicao': cat['ordem']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria de Entrada "{obj.nome}" criada.'))

        # 3. Categorias Financeiras (Saídas)
        saidas = [
            # Deduções
            {'nome': 'Impostos sobre Vendas', 'grupo_dre': 'Deduções da Receita Bruta', 'ordem': 30},
            # Custos
            {'nome': 'Custo de Produtos Vendidos (CPV)', 'grupo_dre': 'Custos (CPV/CSP)', 'ordem': 40},
            {'nome': 'Custo de Serviços Prestados (CSP)', 'grupo_dre': 'Custos (CPV/CSP)', 'ordem': 50},
            # Despesas Operacionais
            {'nome': 'Salários e Proventos', 'grupo_dre': 'Despesas com Pessoal', 'ordem': 60},
            {'nome': 'Encargos Sociais', 'grupo_dre': 'Despesas com Pessoal', 'ordem': 70},
            {'nome': 'Aluguel / Condomínio', 'grupo_dre': 'Despesas Administrativas', 'ordem': 80},
            {'nome': 'Energia / Água / Internet', 'grupo_dre': 'Despesas Administrativas', 'ordem': 90},
            {'nome': 'Material de Escritório', 'grupo_dre': 'Despesas Administrativas', 'ordem': 100},
            {'nome': 'Marketing e Publicidade', 'grupo_dre': 'Despesas Comerciais', 'ordem': 110},
            {'nome': 'Comissões de Vendas', 'grupo_dre': 'Despesas Comerciais', 'ordem': 120},
            {'nome': 'Tarifas Bancárias', 'grupo_dre': 'Resultado Financeiro', 'ordem': 130},
            {'nome': 'Juros e Multas Pagos', 'grupo_dre': 'Resultado Financeiro', 'ordem': 140},
        ]

        for cat in saidas:
            obj, created = CategoriaFinanceira.objects.get_or_create(
                nome=cat['nome'],
                tipo='saida',
                defaults={
                    'grupo_dre': cat['grupo_dre'],
                    'ordem_exibicao': cat['ordem']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria de Saída "{obj.nome}" criada.'))

        self.stdout.write(self.style.SUCCESS('Inicialização de dados financeiros concluída com sucesso!'))
