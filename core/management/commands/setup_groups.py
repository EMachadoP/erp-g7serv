from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Cria os grupos de acesso iniciais do sistema'

    def handle(self, *args, **options):
        groups_data = {
            'SÓCIO-DIRETOR': 'Acesso Total ao Sistema',
            'ADMINISTRATIVO COMERCIAL': 'Acesso a Vendas, Contratos e Clientes',
            'SUPERVISOR TÉCNICO': 'Acesso a OS, Relatórios e Estoque',
            'TÉCNICO': 'Acesso restrito a OS e Mobile'
        }

        for name, desc in groups_data.items():
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{name}" criado com sucesso.'))
            else:
                self.stdout.write(f'Grupo "{name}" já existe.')

        # Assign permissions (Basic logic)
        # SÓCIO-DIRETOR gets all permissions
        socio_group = Group.objects.get(name='SÓCIO-DIRETOR')
        socio_group.permissions.set(Permission.objects.all())
        self.stdout.write(self.style.SUCCESS('Permissões atribuídas ao SÓCIO-DIRETOR.'))

        self.stdout.write(self.style.SUCCESS('Configuração de grupos concluída.'))
