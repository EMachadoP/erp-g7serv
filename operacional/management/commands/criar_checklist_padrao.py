from django.core.management.base import BaseCommand
from operacional.models import ChecklistCategoria, ChecklistPergunta

class Command(BaseCommand):
    help = 'Cria a estrutura de checklist padrão para manutenção preventiva.'

    def handle(self, *args, **options):
        checklist_data = {
            'Dados Gerais': ['Nome do Porteiro'],
            'CFTV': [
                'Quantos DVR?', 'Modelo', 'ID', 'Login', 'Senha Padrão?',
                'Câmeras Funcionando?', 'DVR Limpo?', 'Gravando?',
                'Dias de Gravação', 'Imagens Nítidas?', 'Precisa Orçamento?'
            ],
            'Alarme': [
                'Sensores Funcionando?', 'Central Ativa?', 'Limpa?', 'Fios Expostos?'
            ],
            'Cerca Elétrica': [
                'Funcionando?', 'Pulsando?', 'Fios Partidos?', 'Hastes OK?'
            ],
            'Motores': [
                'Quantos?', 'Marca/Modelo', 'Limpo?', 'Cremalheira Fixa?',
                'Roldanas?', 'Controle OK?', 'Fim de Curso?', 'Antiesmagamento?',
                'Fio Exposto?', 'Sinaleira?', 'Controle Acesso?', 'LED Ativo?'
            ],
            'Portão Pedestre': [
                'Fecho/Fechadura?', 'Botoeira?', 'Fechamento?', 'Mola?',
                'Alerta Sonoro?', 'Intertravamento?'
            ],
            'Antenas': [
                'Módulo Ativo?', 'Sinal nos Apts?', 'Organizada?', 'Fios Expostos?'
            ],
            'Interfones': [
                'Organizada?', 'Funcionando?', 'Identificador?'
            ]
        }

        order_cat = 10
        for category_name, questions in checklist_data.items():
            category, created = ChecklistCategoria.objects.get_or_create(
                name=category_name,
                defaults={'order': order_cat}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria "{category_name}" criada.'))
            
            order_per = 10
            for question_text in questions:
                # Determine type
                # Standard is Sim/Não/ND unless it's a field for data
                q_type = 'options'
                if any(x in question_text.lower() for x in ['nome', 'modelo', 'id', 'login', 'marca', 'quantos', 'dias']):
                    q_type = 'text' if 'quantos' not in question_text.lower() and 'dias' not in question_text.lower() else 'number'

                pergunta, p_created = ChecklistPergunta.objects.get_or_create(
                    categoria=category,
                    texto=question_text,
                    defaults={
                        'tipo': q_type,
                        'order': order_per
                    }
                )
                if p_created:
                    self.stdout.write(f'  - Pergunta "{question_text}" criada ({q_type}).')
                
                order_per += 10
            order_cat += 10

        self.stdout.write(self.style.SUCCESS('Estrutura de checklist padrão finalizada!'))
