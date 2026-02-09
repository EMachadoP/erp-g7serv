from django.db import models
from ckeditor.fields import RichTextField
from core.models import Person
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True

class BillingGroup(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome do Grupo")
    due_day = models.IntegerField(null=True, blank=True, verbose_name="Dia de Vencimento Padrão")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupo de Faturamento"
        verbose_name_plural = "Grupos de Faturamento"

class ContractTemplate(BaseModel):
    TEMPLATE_TYPE_CHOICES = (
        ('Novo Contrato', 'Novo Contrato'),
        ('Cancelamento', 'Cancelamento'),
        ('Reajuste', 'Reajuste'),
        ('Aditivos', 'Aditivos'),
    )

    name = models.CharField(max_length=255, verbose_name="Nome do Modelo")
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, default='Novo Contrato', verbose_name="Tipo de Modelo")
    content = RichTextField(verbose_name="Conteúdo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Modelo de Contrato"
        verbose_name_plural = "Modelos de Contrato"

class Contract(BaseModel):
    MODALITY_CHOICES = (
        ('Mensal', 'Mensal'),
        ('Anual', 'Anual'),
    )
    STATUS_CHOICES = (
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Cancelado', 'Cancelado'),
        ('Expirado', 'Expirado'),
    )

    client = models.ForeignKey(Person, on_delete=models.CASCADE, limit_choices_to={'is_client': True}, verbose_name="Cliente")
    budget = models.ForeignKey('Budget', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Orçamento Origem")
    template = models.ForeignKey(ContractTemplate, on_delete=models.PROTECT, verbose_name="Modelo de Contrato")
    billing_group = models.ForeignKey(BillingGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Grupo de Faturamento")
    
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='Mensal', verbose_name="Modalidade")
    due_day = models.IntegerField(verbose_name="Dia de Vencimento")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ativo', verbose_name="Status")
    
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data de Término")
    next_readjustment_date = models.DateField(null=True, blank=True, verbose_name="Próximo Reajuste")

    # Digital Signature
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True, verbose_name="Assinatura")
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name="Assinado em")
    signed_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP da Assinatura")

    def __str__(self):
        return f"Contrato {self.id} - {self.client.name}"

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

class Service(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome do Serviço")
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo Base")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

class Budget(BaseModel):
    STATUS_CHOICES = (
        ('Aberto', 'Aberto'),
        ('Ganho', 'Ganho'),
        ('Perdido', 'Perdido'),
        ('Cancelado', 'Cancelado'),
        ('Vencido', 'Vencido'),
    )
    
    FOLLOWUP_CHOICES = (
        ('Manual', 'Manual'),
        ('Automatico', 'Automático'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('PIX', 'PIX'),
        ('BOLETO', 'Boleto'),
        ('CARTAO', 'Cartão de Crédito'),
        ('OUTRO', 'Outro'),
    )

    client = models.ForeignKey(Person, on_delete=models.CASCADE, limit_choices_to={'is_client': True}, verbose_name="Cliente")
    title = models.CharField(max_length=255, verbose_name="Título", blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vendedor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aberto', verbose_name="Status")
    approved_by_operations = models.BooleanField(default=False, verbose_name="Liberado pelo Operacional")
    followup_strategy = models.CharField(max_length=20, choices=FOLLOWUP_CHOICES, default='Manual', verbose_name="Estratégia de Follow-up")
    last_followup = models.DateTimeField(null=True, blank=True, verbose_name="Último Follow-up")
    date = models.DateField(verbose_name="Data de Abertura")
    validity_date = models.DateField(null=True, blank=True, verbose_name="Validade")
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='OUTRO', verbose_name="Forma de Pagamento")
    payment_details = models.TextField(blank=True, null=True, verbose_name="Detalhes do Pagamento")
    observation = RichTextField(blank=True, null=True, verbose_name="Observações")
    
    # Address info (snapshot)
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    contact = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contato")

    def __str__(self):
        return f"Orçamento {self.id} - {self.client.name}"

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"

class BudgetProduct(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey('estoque.Product', on_delete=models.CASCADE, verbose_name="Produto")
    quantity = models.IntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Total")

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class BudgetService(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Serviço")
    quantity = models.IntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Total")

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class ContractItem(BaseModel):
    CATEGORY_CHOICES = (
        ('MANUTENCAO', 'Manutenção Mensal'),
        ('MONITORAMENTO', 'Monitoramento'),
        ('PONTO', 'Ponto Eletrônico'),
        ('COMODATO', 'Comodato Equipamentos'),
        ('OUTROS', 'Outros'),
    )

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='items', verbose_name="Contrato")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MANUTENCAO', verbose_name="Categoria")
    financial_category = models.ForeignKey('financeiro.CategoriaFinanceira', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria Financeira (DRE)")
    description = models.CharField(max_length=255, verbose_name="Descrição")
    quantity = models.IntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Unitário")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")

    def save(self, *args, **kwargs):
        self.total_price = (self.quantity or 1) * (self.unit_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_category_display()} - {self.description}"


class ContractReadjustment(BaseModel):
    STATUS_CHOICES = (
        ('APPLIED', 'Aplicado'),
        ('CANCELLED', 'Cancelado'),
        ('DEFERRED', 'Adiado'),
    )
    
    TYPE_CHOICES = (
        ('READJUSTMENT', 'Reajuste'),
        ('DEFERRAL', 'Adiamento'),
    )
    
    date = models.DateTimeField(default=timezone.now, verbose_name="Data do Reajuste")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Percentual (%)")
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Aplicado por")
    readjustment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='READJUSTMENT', verbose_name="Tipo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED', verbose_name="Status")
    observation = models.TextField(blank=True, null=True, verbose_name="Observações")

    def __str__(self):
        return f"Reajuste {self.id} - {self.percentage}% em {self.date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Reajuste de Contrato"
        verbose_name_plural = "Reajustes de Contrato"

class ContractReadjustmentLog(models.Model):
    readjustment = models.ForeignKey(ContractReadjustment, on_delete=models.CASCADE, related_name='logs')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    
    # Snapshots
    old_value = models.DecimalField(max_digits=10, decimal_places=2)
    new_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store items snapshot as JSON or similar if needed, but for now we focus on values
    # We'll save the old item prices to allow rollback
    items_snapshot = models.JSONField(verbose_name="Snapshot dos Itens", help_text="Armazena IDs e valores unitários antigos")

    def __str__(self):
        return f"Log Reajuste {self.readjustment.id} - Contrato {self.contract.id}"
