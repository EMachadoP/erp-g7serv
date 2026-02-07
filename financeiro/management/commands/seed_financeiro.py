from django.core.management.base import BaseCommand
from financeiro.models import CategoriaFinanceira, CentroResultado

class Command(BaseCommand):
    help = 'Popula categorias financeiras para DRE'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando carga de dados financeiros...')
        
        # Criar Centros de Resultado
        centros = ['Operacional', 'Comercial', 'Administrativo']
        for c in centros:
            obj, created = CentroResultado.objects.get_or_create(nome=c)
            if created:
                self.stdout.write(f'Centro de Resultado created: {c}')

        # Criar Categorias conforme Passo 2 e 4
        categorias = [
            # Grupo 1: Receita Bruta
            ('Venda de Serviços', 'entrada', '1. Receita Bruta', 1, None),
            ('Venda de Produtos', 'entrada', '1. Receita Bruta', 2, None),
            
            # Grupo 2: Deduções
            ('Simples Nacional (DAS)', 'saida', '2. Deduções', 3, None),
            ('Cancelamentos/Devoluções', 'saida', '2. Deduções', 4, None),
            
            # Grupo 3: Custos Variáveis
            ('Materiais e Insumos', 'saida', '3. Custos Variáveis', 5, None),
            ('Logística e Fretes', 'saida', '3. Custos Variáveis', 6, None),
            ('Mão de Obra Terceirizada', 'saida', '3. Custos Variáveis', 7, None),
            
            # Grupo 4: Despesas Fixas (OPEX)
            ('Pro-labore e Salários', 'saida', '4. Despesas Fixas (OPEX)', 8, None),
            ('Encargos Sociais', 'saida', '4. Despesas Fixas (OPEX)', 9, None),
            ('Aluguel e Condomínio', 'saida', '4. Despesas Fixas (OPEX)', 10, None),
            ('Softwares e Assinaturas', 'saida', '4. Despesas Fixas (OPEX)', 11, None),
            ('Marketing e Vendas', 'saida', '4. Despesas Fixas (OPEX)', 12, None),
            ('Contabilidade', 'saida', '4. Despesas Fixas (OPEX)', 13, None),
            
            # Grupo 5: Resultado Financeiro
            ('Tarifas Bancárias', 'saida', '5. Resultado Financeiro', 14, None),
            ('Juros e Multas Pagos', 'saida', '5. Resultado Financeiro', 15, None),
            ('Rendimentos de Aplicação', 'entrada', '5. Resultado Financeiro', 16, None),
        ]
        
        # Mapeamento do Passo 4 (Resumido para o comando de exemplo)
        # Eu usei a lista expandida do Passo 2 para ser mais completo
        
        for nome, tipo, grupo, ordem, pai_nome in categorias:
            pai = None
            if pai_nome:
                pai = CategoriaFinanceira.objects.filter(nome=pai_nome).first()
                
            obj, created = CategoriaFinanceira.objects.get_or_create(
                nome=nome, 
                tipo=tipo, 
                grupo_dre=grupo, 
                defaults={'ordem_exibicao': ordem, 'parent': pai}
            )
            if created:
                self.stdout.write(f'Categoria created: {nome} ({grupo})')
            else:
                # Update fields if already exists
                obj.ordem_exibicao = ordem
                obj.grupo_dre = grupo
                obj.tipo = tipo
                obj.save()
        
        self.stdout.write(self.style.SUCCESS('Plano de Contas DRE G7Serv criado!'))
