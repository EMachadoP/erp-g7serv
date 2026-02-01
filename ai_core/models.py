from django.db import models

class AtendimentoAI(models.Model):
    CATEGORIAS = [
        ('orcamento', 'Orçamento/Comercial'),
        ('suporte', 'Suporte Técnico/OS'),
        ('financeiro', 'Financeiro/Boletos'),
        ('outro', 'Outros Assuntos'),
    ]
    timestamp = models.DateTimeField(auto_now_add=True)
    cliente_nome = models.CharField(max_length=100, default="Anônimo")
    mensagem_usuario = models.TextField()
    categoria_detectada = models.CharField(max_length=20, choices=CATEGORIAS)
    protocolo = models.CharField(max_length=20, unique=True)
    resolvido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.protocolo} - {self.categoria_detectada}"
