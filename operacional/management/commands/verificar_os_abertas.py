from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from operacional.models import ServiceOrder
from core.models import Notification
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Verifica OS em execução há muito tempo e notifica os técnicos.'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(hours=4)
        
        # OS In Progress started before 4 hours ago
        stale_os = ServiceOrder.objects.filter(
            status='IN_PROGRESS', 
            checkin_time__lt=threshold
        )
        
        count = 0
        for os in stale_os:
            tech_person = os.technical_team
            if tech_person and tech_person.email:
                # Find User
                try:
                    user = User.objects.get(email=tech_person.email)
                    
                    # Check if notification already exists to avoid spam (optional, distinct by day?)
                    # For now, simple check
                    msg = f"Você tem uma OS em execução há mais de 4 horas: OS #{os.id} - {os.client}. Não esqueça de finalizar!"
                    
                    exists = Notification.objects.filter(
                        user=user, 
                        message=msg, 
                        read=False,
                        created_at__gte=timezone.now().date() # Today
                    ).exists()
                    
                    if not exists:
                        Notification.objects.create(
                            user=user,
                            message=msg
                        )
                        count += 1
                        self.stdout.write(f"Notificação enviada para {user.username} (OS #{os.id})")
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Usuário não encontrado para o técnico {tech_person.name} ({tech_person.email})"))
            else:
                self.stdout.write(self.style.WARNING(f"OS #{os.id} sem técnico ou email definido."))
                
        self.stdout.write(self.style.SUCCESS(f"Verificação concluída. {count} notificações geradas."))
