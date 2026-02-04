from django.db import models
from core.models import Person
from nfse_nacional.models import NFSe

class CoraConfig(models.Model):
    AMBIENTE_CHOICES = (
        (1, 'Produção'),
        (2, 'Homologação'),
    )

    client_id = models.CharField(max_length=255, verbose_name="Client ID")
    client_secret = models.CharField(max_length=255, verbose_name="Client Secret", blank=True, null=True)
    certificado_pem = models.FileField(upload_to='cora_certs/', verbose_name="Certificado PEM", blank=True, null=True)
    chave_privada = models.FileField(upload_to='cora_certs/', verbose_name="Chave Privada", blank=True, null=True)
    access_token = models.TextField(blank=True, null=True, verbose_name="Access Token")
    token_expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Token Expira em")
    ambiente = models.IntegerField(choices=AMBIENTE_CHOICES, default=2, verbose_name="Ambiente")
    
    # Configurações de Boleto
    taxa_multa = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00, 
        verbose_name="Taxa de Multa (%)", 
        help_text="Percentual de multa por atraso (ex: 2.00 para 2%)"
    )
    taxa_juros = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.00, 
        verbose_name="Taxa de Juros (% a.m.)", 
        help_text="Percentual de juros ao mês (ex: 1.00 para 1% a.m.)"
    )
    dias_protesto = models.IntegerField(
        default=0, verbose_name="Dias para Protesto",
        help_text="Dias após vencimento para protesto (0 = sem protesto)"
    )
    instrucoes_boleto = models.TextField(
        blank=True, null=True, verbose_name="Instruções do Boleto",
        help_text="Instruções que aparecerão no boleto para o pagador",
        default="Pagável em qualquer banco até o vencimento.\nApós o vencimento cobrar multa e juros."
    )

    def __str__(self):
        return f"Configuração Cora ({self.get_ambiente_display()})"

    class Meta:
        verbose_name = "Configuração Cora"
        verbose_name_plural = "Configuração Cora"

    def save(self, *args, **kwargs):
        if not self.pk and CoraConfig.objects.exists():
            # If you want to ensure it's a singleton, you can raise an error or handle it.
            # For simplicity, we allow saving but typically there should be only one.
            pass
        super(CoraConfig, self).save(*args, **kwargs)

class BoletoCora(models.Model):
    STATUS_CHOICES = (
        ('Aberto', 'Aberto'),
        ('Pago', 'Pago'),
        ('Cancelado', 'Cancelado'),
        ('Atrasado', 'Atrasado'),
    )

    nfse = models.ForeignKey(NFSe, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="NFS-e", related_name="boletos_cora")
    cliente = models.ForeignKey(Person, on_delete=models.PROTECT, verbose_name="Cliente", related_name="boletos_cora")
    cora_id = models.CharField(max_length=100, unique=True, verbose_name="ID Cora")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aberto', verbose_name="Status")
    linha_digitavel = models.CharField(max_length=255, blank=True, null=True, verbose_name="Linha Digitável")
    codigo_barras = models.CharField(max_length=255, blank=True, null=True, verbose_name="Código de Barras")
    url_pdf = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL do PDF")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return f"Boleto {self.cora_id} - {self.cliente.name} - R$ {self.valor}"

    class Meta:
        verbose_name = "Boleto Cora"
        verbose_name_plural = "Boletos Cora"
