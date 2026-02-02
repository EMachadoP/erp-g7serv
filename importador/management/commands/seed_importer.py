from django.core.management.base import BaseCommand
from importador.models import ModuleField

class Command(BaseCommand):
    help = 'Seeds initial module fields for the Intelligent Importer'

    def handle(self, *args, **options):
        fields = [
            # Contas a Pagar
            {'module_type': 'contas_pagar', 'field_name': 'data_vencimento', 'field_label': 'Data de Vencimento', 'field_type': 'date', 'required': True, 'order': 1},
            {'module_type': 'contas_pagar', 'field_name': 'valor', 'field_label': 'Valor', 'field_type': 'currency', 'required': True, 'order': 2},
            {'module_type': 'contas_pagar', 'field_name': 'descricao', 'field_label': 'Descrição / Favorecido', 'field_type': 'string', 'required': True, 'order': 3},
            {'module_type': 'contas_pagar', 'field_name': 'documento', 'field_label': 'Nº Documento', 'field_type': 'string', 'required': False, 'order': 4},
            {'module_type': 'contas_pagar', 'field_name': 'categoria', 'field_label': 'Categoria', 'field_type': 'string', 'required': False, 'order': 5},
            
            # Contas a Receber
            {'module_type': 'contas_receber', 'field_name': 'data_vencimento', 'field_label': 'Data de Vencimento', 'field_type': 'date', 'required': True, 'order': 1},
            {'module_type': 'contas_receber', 'field_name': 'valor', 'field_label': 'Valor total', 'field_type': 'currency', 'required': True, 'order': 2},
            {'module_type': 'contas_receber', 'field_name': 'cliente', 'field_label': 'Cliente', 'field_type': 'string', 'required': True, 'order': 3},
            {'module_type': 'contas_receber', 'field_name': 'status', 'field_label': 'Status', 'field_type': 'string', 'required': False, 'order': 4},
            
            # Estoque
            {'module_type': 'estoque', 'field_name': 'produto', 'field_label': 'Nome do Produto', 'field_type': 'string', 'required': True, 'order': 1},
            {'module_type': 'estoque', 'field_name': 'quantidade', 'field_label': 'Quantidade em Estoque', 'field_type': 'number', 'required': True, 'order': 2},
            {'module_type': 'estoque', 'field_name': 'preco_custo', 'field_label': 'Preço de Custo', 'field_type': 'currency', 'required': False, 'order': 3},
            {'module_type': 'estoque', 'field_name': 'codigo_barras', 'field_label': 'Código de Barras/EAN', 'field_type': 'string', 'required': False, 'order': 4},

            # Ordem de Serviço (OS)
            {'module_type': 'os', 'field_name': 'numero_os', 'field_label': 'Nº OS', 'field_type': 'string', 'required': True, 'order': 1},
            {'module_type': 'os', 'field_name': 'cliente', 'field_label': 'Cliente', 'field_type': 'string', 'required': True, 'order': 2},
            {'module_type': 'os', 'field_name': 'equipamento', 'field_label': 'Equipamento', 'field_type': 'string', 'required': False, 'order': 3},
            {'module_type': 'os', 'field_name': 'data_abertura', 'field_label': 'Data Abertura', 'field_type': 'date', 'required': True, 'order': 4},
            {'module_type': 'os', 'field_name': 'status', 'field_label': 'Status', 'field_type': 'string', 'required': False, 'order': 5},
            {'module_type': 'os', 'field_name': 'prioridade', 'field_label': 'Prioridade', 'field_type': 'string', 'required': False, 'order': 6},
            {'module_type': 'os', 'field_name': 'valor_total', 'field_label': 'Valor Total', 'field_type': 'currency', 'required': False, 'order': 7},
            {'module_type': 'os', 'field_name': 'tecnico', 'field_label': 'Técnico', 'field_type': 'string', 'required': False, 'order': 8},

            # Clientes
            {'module_type': 'clientes', 'field_name': 'nome', 'field_label': 'Nome/Razão Social', 'field_type': 'string', 'required': True, 'order': 1},
            {'module_type': 'clientes', 'field_name': 'cpf_cnpj', 'field_label': 'CPF/CNPJ', 'field_type': 'cnpj', 'required': True, 'order': 2},
            {'module_type': 'clientes', 'field_name': 'rg_ie', 'field_label': 'RG/Inscrição Estadual', 'field_type': 'string', 'required': False, 'order': 3},
            {'module_type': 'clientes', 'field_name': 'telefone', 'field_label': 'Telefone', 'field_type': 'string', 'required': False, 'order': 4},
            {'module_type': 'clientes', 'field_name': 'email', 'field_label': 'Email', 'field_type': 'string', 'required': False, 'order': 5},
            {'module_type': 'clientes', 'field_name': 'endereco', 'field_label': 'Endereço', 'field_type': 'text', 'required': False, 'order': 6},
            {'module_type': 'clientes', 'field_name': 'status', 'field_label': 'Status', 'field_type': 'string', 'required': False, 'order': 7},
            {'module_type': 'clientes', 'field_name': 'contato_nome', 'field_label': 'Nome do Contato', 'field_type': 'string', 'required': False, 'order': 8},
            {'module_type': 'clientes', 'field_name': 'contato_telefone', 'field_label': 'Telefone do Contato', 'field_type': 'string', 'required': False, 'order': 9},
            {'module_type': 'clientes', 'field_name': 'contato_email', 'field_label': 'Email do Contato', 'field_type': 'string', 'required': False, 'order': 10},
            {'module_type': 'clientes', 'field_name': 'contato_tipo', 'field_label': 'Tipo do Contato', 'field_type': 'string', 'required': False, 'order': 11},

            # Orçamentos
            {'module_type': 'orcamentos', 'field_name': 'numero_orcamento', 'field_label': 'Nº Orçamento', 'field_type': 'string', 'required': True, 'order': 1},
            {'module_type': 'orcamentos', 'field_name': 'cliente', 'field_label': 'Cliente', 'field_type': 'string', 'required': True, 'order': 2},
            {'module_type': 'orcamentos', 'field_name': 'data_emissao', 'field_label': 'Data Emissão', 'field_type': 'date', 'required': True, 'order': 3},
            {'module_type': 'orcamentos', 'field_name': 'data_validade', 'field_label': 'Data Validade', 'field_type': 'date', 'required': False, 'order': 4},
            {'module_type': 'orcamentos', 'field_name': 'valor_total', 'field_label': 'Valor Total', 'field_type': 'currency', 'required': True, 'order': 5},
            {'module_type': 'orcamentos', 'field_name': 'status', 'field_label': 'Status', 'field_type': 'string', 'required': False, 'order': 6},
            {'module_type': 'orcamentos', 'field_name': 'descricao', 'field_label': 'Descrição', 'field_type': 'text', 'required': False, 'order': 7},
            {'module_type': 'orcamentos', 'field_name': 'vendedor', 'field_label': 'Vendedor', 'field_type': 'string', 'required': False, 'order': 8},

            # Contratos
            {'module_type': 'contratos', 'field_name': 'numero_contrato', 'field_label': 'Nº Contrato', 'field_type': 'string', 'required': True, 'order': 1},
            {'module_type': 'contratos', 'field_name': 'cliente', 'field_label': 'Cliente', 'field_type': 'string', 'required': True, 'order': 2},
            {'module_type': 'contratos', 'field_name': 'tipo_contrato', 'field_label': 'Tipo de Contrato', 'field_type': 'string', 'required': False, 'order': 3},
            {'module_type': 'contratos', 'field_name': 'data_inicio', 'field_label': 'Data Início', 'field_type': 'date', 'required': True, 'order': 4},
            {'module_type': 'contratos', 'field_name': 'data_fim', 'field_label': 'Data Fim', 'field_type': 'date', 'required': False, 'order': 5},
            {'module_type': 'contratos', 'field_name': 'dia_cobranca', 'field_label': 'Dia de Cobrança', 'field_type': 'string', 'required': False, 'order': 6},
            {'module_type': 'contratos', 'field_name': 'grupo_faturamento', 'field_label': 'Grupo de Faturamento', 'field_type': 'string', 'required': False, 'order': 7},
            {'module_type': 'contratos', 'field_name': 'forma_pagamento', 'field_label': 'Forma de Pagamento', 'field_type': 'string', 'required': False, 'order': 8},
            {'module_type': 'contratos', 'field_name': 'indice_reajuste', 'field_label': 'Índice de Reajuste', 'field_type': 'string', 'required': False, 'order': 9},
            {'module_type': 'contratos', 'field_name': 'status', 'field_label': 'Status', 'field_type': 'string', 'required': False, 'order': 10},
            {'module_type': 'contratos', 'field_name': 'valor_mensal', 'field_label': 'Valor Mensal', 'field_type': 'currency', 'required': False, 'order': 11},
            {'module_type': 'contratos', 'field_name': 'servico_principal', 'field_label': 'Serviço Principal', 'field_type': 'string', 'required': False, 'order': 12},
        ]

        for field_data in fields:
            ModuleField.objects.get_or_create(
                module_type=field_data['module_type'],
                field_name=field_data['field_name'],
                defaults=field_data
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(fields)} fields'))
