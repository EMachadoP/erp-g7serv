from django.db import models
from django.db.models import Max

from core.models import Person, Service

class Empresa(models.Model):
    AMBIENTE_CHOICES = (
        (1, 'Produção'),
        (2, 'Homologação'),
    )

    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ")
    inscricao_municipal = models.CharField(max_length=20, verbose_name="Inscrição Municipal")
    codigo_mun_ibge = models.CharField(max_length=7, verbose_name="Código Município IBGE", default="2611606", help_text="Ex: 2611606 (Recife)")
    certificado_a1 = models.FileField(upload_to='certificados/', verbose_name="Certificado Digital A1 (.pfx)")
    senha_certificado = models.CharField(max_length=100, verbose_name="Senha do Certificado")
    ambiente = models.IntegerField(choices=AMBIENTE_CHOICES, default=2, verbose_name="Ambiente")

    def __str__(self):
        return self.razao_social

    class Meta:
        verbose_name = "Empresa Emissora"
        verbose_name_plural = "Empresas Emissoras"

class NFSe(models.Model):
    STATUS_CHOICES = (
        ('Pendente', 'Pendente'),
        ('Autorizada', 'Autorizada'),
        ('Rejeitada', 'Rejeitada'),
    )

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, verbose_name="Empresa Emissora")
    cliente = models.ForeignKey(Person, on_delete=models.PROTECT, verbose_name="Tomador", limit_choices_to={'is_client': True})
    servico = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Serviço")
    
    numero_dps = models.IntegerField(verbose_name="Número DPS", editable=False)
    serie_dps = models.CharField(max_length=5, default='1', verbose_name="Série DPS")
    data_emissao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Emissão")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente', verbose_name="Status")
    
    chave_acesso = models.CharField(max_length=50, blank=True, null=True, verbose_name="Chave de Acesso")
    xml_envio = models.TextField(blank=True, null=True, verbose_name="XML Envio")
    xml_retorno = models.TextField(blank=True, null=True, verbose_name="XML Retorno")
    xml_envio = models.TextField(blank=True, null=True, verbose_name="XML Envio")
    xml_retorno = models.TextField(blank=True, null=True, verbose_name="XML Retorno")
    json_erro = models.JSONField(blank=True, null=True, verbose_name="JSON Erro")
    
    # Override fields from Service/Invoice
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor do Serviço (Override)")
    descricao_servico = models.TextField(null=True, blank=True, verbose_name="Descrição do Serviço (Override)")

    def save(self, *args, **kwargs):
        if not self.numero_dps:
            # Get the maximum numero_dps for the current company and series
            max_numero = NFSe.objects.filter(
                empresa=self.empresa, 
                serie_dps=self.serie_dps
            ).aggregate(Max('numero_dps'))['numero_dps__max']
            
            self.numero_dps = (max_numero or 0) + 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"DPS {self.numero_dps} - {self.cliente.name}"

    class Meta:
        verbose_name = "NFS-e Nacional"
        verbose_name_plural = "NFS-e Nacional"
        unique_together = ('empresa', 'serie_dps', 'numero_dps')
