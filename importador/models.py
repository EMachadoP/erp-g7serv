from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class ImportStatus(models.TextChoices):
    PENDING = 'pending', _('Pendente')
    PROCESSING = 'processing', _('Processando')
    COMPLETED = 'completed', _('Concluído')
    ERROR = 'error', _('Erro')
    CANCELLED = 'cancelled', _('Cancelado')

class ModuleField(models.Model):
    """Define os campos disponíveis para cada módulo"""
    module_type = models.CharField(max_length=50, db_index=True)
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50)  # string, number, date, currency, boolean, text
    
    # Validações
    required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    is_searchable = models.BooleanField(default=True)
    
    # Configurações
    default_value = models.CharField(max_length=255, null=True, blank=True)
    validation_rules = models.JSONField(null=True, blank=True)  # min, max, regex, etc
    options = models.JSONField(null=True, blank=True)  # Para campos com opções fixas
    
    # Ordenação
    order = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Campo do Módulo')
        verbose_name_plural = _('Campos do Módulo')
        ordering = ['module_type', 'order']

    def __str__(self):
        return f"{self.module_type}.{self.field_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "module_type": self.module_type,
            "field_name": self.field_name,
            "field_label": self.field_label,
            "field_type": self.field_type,
            "required": self.required,
            "is_unique": self.is_unique,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "options": self.options,
            "order": self.order,
        }

class ImportTemplate(models.Model):
    """Template de importação mapeado"""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    module_type = models.CharField(max_length=50, db_index=True)
    
    # Configurações de leitura (Pandas)
    file_type = models.CharField(max_length=10, default="xlsx")  # xlsx, csv
    delimiter = models.CharField(max_length=5, default=",")
    encoding = models.CharField(max_length=20, default="utf-8")
    skip_rows = models.IntegerField(default=0)
    header_row = models.IntegerField(default=0)
    
    # Mapeamento: {coluna_planilha: campo_sistema}
    mapping = models.JSONField()
    # Tipos de colunas detectados/forçados: {coluna: tipo}
    column_types = models.JSONField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Template de Importação')
        verbose_name_plural = _('Templates de Importação')

    def __str__(self):
        return self.name

class ImportJob(models.Model):
    """Job de importação executado"""
    template = models.ForeignKey(ImportTemplate, on_delete=models.CASCADE, related_name='jobs')
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=ImportStatus.choices, 
        default=ImportStatus.PENDING
    )
    
    # Estatísticas
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    inserted_rows = models.IntegerField(default=0)
    updated_rows = models.IntegerField(default=0)
    
    # Logs
    errors_log = models.JSONField(null=True, blank=True, default=list)
    warnings_log = models.JSONField(null=True, blank=True, default=list)
    validation_results = models.JSONField(null=True, blank=True)
    
    # Timestamps
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Flags
    dry_run = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Job de Importação')
        verbose_name_plural = _('Jobs de Importação')

    def __str__(self):
        return f"{self.id} - {self.status} - {self.original_filename}"

    def update_status(self, status):
        self.status = status
        if status == ImportStatus.PROCESSING:
            self.processing_started_at = timezone.now()
        elif status in [ImportStatus.COMPLETED, ImportStatus.ERROR]:
            self.completed_at = timezone.now()
        self.save()

    def add_error(self, row_number, column, message, value=None):
        if not self.errors_log:
            self.errors_log = []
        self.errors_log.append({
            "row": row_number,
            "column": column,
            "message": message,
            "value": str(value) if value is not None else None,
            "timestamp": timezone.now().isoformat()
        })
        self.error_rows += 1
        self.save()

    def get_progress_percentage(self):
        if self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)

    def get_success_rate(self):
        if self.processed_rows == 0:
            return 0.0
        success = self.processed_rows - self.error_rows
        return (success / self.processed_rows) * 100

    def get_error_rate(self):
        if self.processed_rows == 0:
            return 0.0
        return (self.error_rows / self.processed_rows) * 100

class ImportError(models.Model):
    """Erro individual de importação"""
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='errors')
    row_number = models.IntegerField()
    column_name = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField()
    original_value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Erro de Importação')
        verbose_name_plural = _('Erros de Importação')

    def __str__(self):
        return f"Row {self.row_number}: {self.error_message[:50]}"
