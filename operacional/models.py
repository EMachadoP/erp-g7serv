from django.db import models
from core.models import BaseModel, Person
from django.contrib.auth.models import User

class ServiceOrder(BaseModel):
    STATUS_CHOICES = [
        ('INSTALLATION_PENDING', 'Instalação Pendente'),
        ('PENDING', 'Pendente'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('WAITING_MATERIAL', 'Aguardando Material'),
        ('COMPLETED', 'Concluído'),
        ('CANCELED', 'Cancelado'),
    ]

    TYPE_CHOICES = [
        ('Preventiva', 'Manutenção Preventiva'),
        ('Corretiva', 'Manutenção Corretiva'),
        ('Instalacao', 'Instalação'),
        ('Outro', 'Outro'),
    ]

    REASON_CHOICES = [
        ('Solicitacao', 'Solicitação do Cliente'),
        ('Defeito', 'Defeito Apresentado'),
        ('Garantia', 'Garantia'),
        ('Outro', 'Outro'),
    ]

    client = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='service_orders', limit_choices_to={'is_client': True})
    budget = models.ForeignKey('comercial.Budget', on_delete=models.SET_NULL, null=True, blank=True, related_name='service_orders', verbose_name="Orçamento Origem")
    product = models.CharField(max_length=200, help_text="Produto ou Serviço", blank=True, null=True) # Deprecated
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # New Fields
    technical_team = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_orders_team', limit_choices_to={'is_collaborator': True}, verbose_name="Equipe Técnica (Legado)")
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_orders_technician', verbose_name="Técnico Responsável")
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_orders', verbose_name="Vendedor")
    order_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Corretiva', verbose_name="Tipo")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='Solicitacao', verbose_name="Motivo da OS")
    scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="Previsão de Atendimento")
    duration = models.CharField(max_length=50, blank=True, null=True, verbose_name="Duração")
    
    # Address Snapshot
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    contact = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contato")
    
    # Signature
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True, verbose_name="Assinatura Cliente")
    solution = models.TextField(blank=True, null=True, verbose_name="Descrição da Solução")

    # Geo & Time Tracking (Mobile)
    checkin_lat = models.DecimalField(max_digits=20, decimal_places=15, null=True, blank=True, verbose_name="Latitude Check-in")
    checkin_long = models.DecimalField(max_digits=20, decimal_places=15, null=True, blank=True, verbose_name="Longitude Check-in")
    checkin_time = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Check-in")
    checkout_time = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Check-out")

    def __str__(self):
        return f"OS #{self.id} - {self.client.name}"

class OSAnexo(BaseModel):
    TYPE_CHOICES = (
        ('Antes', 'Antes do Serviço'),
        ('Depois', 'Depois do Serviço'),
        ('Diagnostico', 'Diagnóstico/Laudo'),
    )

    os = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='anexos', verbose_name="Ordem de Serviço")
    file = models.ImageField(upload_to='uploads/os_fotos/%Y/%m/', verbose_name="Foto/Anexo")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Diagnostico', verbose_name="Tipo")

    def __str__(self):
        return f"Anexo {self.id} - {self.type}"

    class Meta:
        verbose_name = "Anexo de OS"
        verbose_name_plural = "Anexos de OS"

class ServiceOrderItem(BaseModel):
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Ordem de Serviço")
    product = models.ForeignKey('estoque.Product', on_delete=models.CASCADE, verbose_name="Produto")
    quantity = models.IntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Total", editable=False)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "Item de OS"
        verbose_name_plural = "Itens de OS"

# --- Checklist Models ---

class ChecklistCategoria(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Checklist: Categoria"
        verbose_name_plural = "Checklist: Categorias"
        ordering = ['order', 'name']

class ChecklistPergunta(BaseModel):
    TYPE_CHOICES = (
        ('options', 'Múltipla Escolha (Sim/Não/ND)'),
        ('text', 'Texto Curto'),
        ('number', 'Número'),
    )
    categoria = models.ForeignKey(ChecklistCategoria, on_delete=models.CASCADE, related_name='perguntas', verbose_name="Categoria")
    texto = models.CharField(max_length=255, verbose_name="Pergunta")
    tipo = models.CharField(max_length=20, choices=TYPE_CHOICES, default='options')
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")

    def __str__(self):
        return f"[{self.categoria.name}] {self.texto}"

    class Meta:
        verbose_name = "Checklist: Pergunta"
        verbose_name_plural = "Checklist: Perguntas"
        ordering = ['categoria__order', 'order']

def checklist_photo_path(instance, filename):
    # Upload to uploads/checklist/{id_os}/{filename}
    return f'uploads/checklist/{instance.os.id}/{filename}'

class ChecklistResposta(BaseModel):
    os = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='checklist_respostas', verbose_name="Ordem de Serviço")
    pergunta = models.ForeignKey(ChecklistPergunta, on_delete=models.CASCADE, verbose_name="Pergunta")
    resposta_valor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Resposta")
    comentario = models.TextField(blank=True, null=True, verbose_name="Observação")
    foto = models.ImageField(upload_to=checklist_photo_path, null=True, blank=True, verbose_name="Foto")

    def __str__(self):
        return f"Resposta OS#{self.os.id} - {self.pergunta.texto}"

    class Meta:
        verbose_name = "Checklist: Resposta"
        verbose_name_plural = "Checklist: Respostas"
        unique_together = ('os', 'pergunta')
