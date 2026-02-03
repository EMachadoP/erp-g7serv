from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True

class Person(BaseModel):
    PERSON_TYPES = (
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    )
    
    name = models.CharField(max_length=255, verbose_name="Razão Social / Nome Completo")
    fantasy_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    person_type = models.CharField(max_length=2, choices=PERSON_TYPES, default='PJ', verbose_name="Tipo de Pessoa")
    document = models.CharField(max_length=20, unique=True, verbose_name="CPF / CNPJ")
    state_registration = models.CharField(max_length=30, blank=True, null=True, verbose_name="Inscrição Estadual")
    
    # Responsible (for PJ)
    responsible_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome do Responsável")
    responsible_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Responsável")
    
    # Flags
    is_client = models.BooleanField(default=False, verbose_name="É Cliente?")
    is_supplier = models.BooleanField(default=False, verbose_name="É Fornecedor?")
    is_collaborator = models.BooleanField(default=False, verbose_name="É Colaborador?")
    is_final_consumer = models.BooleanField(default=False, verbose_name="Consumidor Final?")
    
    # Contact
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    
    # Address
    zip_code = models.CharField(max_length=8, blank=True, null=True, verbose_name="CEP")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Logradouro")
    number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    complement = models.CharField(max_length=255, blank=True, null=True, verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    codigo_municipio_ibge = models.CharField(max_length=7, blank=True, null=True, verbose_name="Código Município IBGE")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    state = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")

    def __str__(self):
        return self.fantasy_name or self.name

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

class Service(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome do Serviço")
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo Base")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")
    
    # NFS-e Fields
    codigo_tributacao_nacional = models.CharField(max_length=20, verbose_name="Código Tributação Nacional", help_text="Ex: 1.07.01", blank=True, null=True)
    codigo_tributacao_municipal = models.CharField(max_length=20, verbose_name="Código Tributação Municipal", help_text="Ex: 14.02.01.501", blank=True, null=True)
    item_nbs = models.CharField(max_length=20, verbose_name="Item NBS", blank=True, null=True)
    codigo_nbs = models.CharField(max_length=9, verbose_name="Código NBS (9 dígitos)", blank=True, null=True)
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Alíquota ISS (%)", default=0)
    description = models.TextField(verbose_name="Descrição Detalhada (NFS-e)", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

class CompanySettings(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome da Empresa")
    cnpj = models.CharField(max_length=20, verbose_name="CNPJ")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="Logo")
    
    # Integrations
    CORA_ENV_CHOICES = [
        ('stage', 'Homologação (Stage)'),
        ('prod', 'Produção'),
    ]
    cora_environment = models.CharField(max_length=10, choices=CORA_ENV_CHOICES, default='stage', verbose_name="Ambiente Cora")
    cora_client_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cora Client ID")
    cora_cert_base64 = models.TextField(blank=True, null=True, verbose_name="Cora Certificado (Base64)")
    cora_key_base64 = models.TextField(blank=True, null=True, verbose_name="Cora Chave Privada (Base64)")
    cora_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Token API Cora (Legado)")
    google_cloud_credentials = models.JSONField(blank=True, null=True, verbose_name="Credenciais Google Cloud")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Configuração da Empresa"
        verbose_name_plural = "Configurações da Empresa"

class Notification(BaseModel):
    from django.contrib.auth.models import User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Usuário")
    message = models.TextField(verbose_name="Mensagem")
    read = models.BooleanField(default=False, verbose_name="Lida?")
    
    def __str__(self):
        return f"Notificação para {self.user.username}"

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-created_at']

class Technician(BaseModel):
    from django.contrib.auth.models import User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='technician_profile', verbose_name="Usuário")
    phone = models.CharField(max_length=20, verbose_name="Telefone", blank=True, null=True)
    calendar_color = models.CharField(max_length=20, default="#0d6efd", verbose_name="Cor na Agenda")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
