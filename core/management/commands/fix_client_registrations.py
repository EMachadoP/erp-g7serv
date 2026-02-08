import re
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Person
from comercial.models import Contract

class Command(BaseCommand):
    help = 'Limpa e completa o cadastro de clientes vinculados a contratos'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Apenas simula as alterações')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        
        # 1. Identificar Pessoas que precisam de limpeza
        # Selecionamos:
        # - Vinculados a contratos
        # - Marcados como clientes
        # - Com IDs temporários ou de importação
        # - Nomes que indicam condomínios
        from django.db.models import Q
        people = Person.objects.filter(
            Q(contract__isnull=False) |
            Q(is_client=True) |
            Q(document__startswith='TEMP-') |
            Q(document__startswith='IMPORT-') |
            Q(name__icontains='CONDOMINIO')
        ).distinct()
        
        self.stdout.write(self.style.SUCCESS(f"Encontrados {people.count()} clientes vinculados a contratos."))
        
        updated_count = 0
        manual_attention = []

        for person in people:
            self.stdout.write(f"Processando: {person.name}...")
            changed = False
            
            # A. Garantir flags básicas para faturamento
            if not person.is_client:
                person.is_client = True
                changed = True
            
            if not person.is_final_consumer:
                person.is_final_consumer = True
                changed = True

            # B. Tipo de Pessoa (Condomínio é PJ)
            if "CONDOMINIO" in person.name.upper() and person.person_type != 'PJ':
                person.person_type = 'PJ'
                changed = True
            
            # C. Parse de Endereço (se estiver tudo em um campo só e os outros vazios)
            if person.address and not any([person.neighborhood, person.city, person.state, person.zip_code]):
                # Padrão: Logradouro, 123 - Bairro, Cidade - UF, 00000000
                # Ex: Rua Conselheiro Nabuco, 150 - Casa Amarela, Recife - PE, 52070010
                address_str = person.address
                
                # Regex robusto
                pattern = r"^(?P<logradouro>.*?),\s*(?P<numero>\d+)?\s*(?:-\s*(?P<bairro>.*?))?,\s*(?P<cidade>.*?)\s*-\s*(?P<uf>[A-Z]{2})(?:,\s*(?P<cep>\d{8}))?$"
                match = re.match(pattern, address_str)
                
                if match:
                    person.address = match.group('logradouro')
                    person.number = match.group('numero') or ""
                    person.neighborhood = match.group('bairro') or ""
                    person.city = match.group('cidade') or ""
                    person.state = match.group('uf') or ""
                    person.zip_code = match.group('cep') or ""
                    changed = True
                    self.stdout.write(self.style.SUCCESS(f"  - Endereço decomposto: {person.city}/{person.state}"))
                else:
                    # Tentar um split mais simples se o regex falhar
                    # Logradouro, Numero - Bairro, Cidade - UF
                    parts = address_str.split(',')
                    if len(parts) >= 3:
                        # Pelo menos tem Logradouro, Numero, Resto
                        self.stdout.write(self.style.WARNING(f"  - Endereço não bateu no regex padrão, tentando split manual..."))

            # D. Identificar necessidade de atenção manual (documento TEMP-)
            if person.document.startswith(('TEMP-', 'IMPORT-')):
                manual_attention.append({
                    'id': person.id,
                    'name': person.name,
                    'current_doc': person.document
                })

            if changed and not dry_run:
                person.save()
                updated_count += 1
            elif changed and dry_run:
                updated_count += 1

        self.stdout.write("="*40)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"SIMULAÇÃO CONCLUÍDA. {updated_count} registros seriam atualizados."))
        else:
            self.stdout.write(self.style.SUCCESS(f"SUCESSO. {updated_count} registros atualizados."))
            
        if manual_attention:
            self.stdout.write(self.style.ERROR(f"\n{len(manual_attention)} clientes ainda possuem documentos temporários:"))
            for item in manual_attention:
                self.stdout.write(f"- [{item['id']}] {item['name']} ({item['current_doc']})")
            self.stdout.write(self.style.WARNING("\nEstes clientes precisam ter o CPF/CNPJ real informado manualmente antes de faturar."))
