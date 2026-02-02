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
        ]

        for field_data in fields:
            ModuleField.objects.get_or_create(
                module_type=field_data['module_type'],
                field_name=field_data['field_name'],
                defaults=field_data
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(fields)} fields'))
