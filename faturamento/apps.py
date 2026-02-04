from django.apps import AppConfig

class FaturamentoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faturamento'

    def ready(self):
        import faturamento.signals
