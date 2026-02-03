from django.db import models
from django.utils import timezone
from core.models import BaseModel, Person

class FinancialCategory(BaseModel):
    TYPE_CHOICES = (
        ('EXPENSE', 'Despesa'),
        ('REVENUE', 'Receita'),
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Tipo")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories', verbose_name="Categoria Pai")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Categoria Financeira"
        verbose_name_plural = "Categorias Financeiras"

class CashAccount(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome da Conta")
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Banco")
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número da Conta")
    agency = models.CharField(max_length=20, blank=True, null=True, verbose_name="Agência")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Inicial")
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Atual")
    
    def __str__(self):
        return f"{self.name} (R$ {self.current_balance})"
    
    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

class FinancialTransaction(BaseModel):
    TRANSACTION_TYPES = (
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
    )
    
    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES, verbose_name="Tipo")
    date = models.DateField(default=timezone.now, verbose_name="Data")
    account = models.ForeignKey(CashAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name="Conta Bancária")
    category = models.ForeignKey(FinancialCategory, on_delete=models.SET_NULL, null=True, verbose_name="Categoria")
    
    # Links optional
    related_payable = models.ForeignKey('AccountPayable', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name="Conta a Pagar Vinculada")
    related_receivable = models.ForeignKey('AccountReceivable', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name="Conta a Receber Vinculada")
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            if self.transaction_type == 'IN':
                self.account.current_balance += self.amount
            else:
                self.account.current_balance -= self.amount
            self.account.save()
            
    def delete(self, *args, **kwargs):
        # Reverse balance update on delete
        if self.transaction_type == 'IN':
            self.account.current_balance -= self.amount
        else:
            self.account.current_balance += self.amount
        self.account.save()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Movimentação Financeira"
        verbose_name_plural = "Movimentações Financeiras"
        ordering = ['-date', '-created_at']

class CostCenter(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nome")
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    
    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name
    
    class Meta:
        verbose_name = "Centro de Resultado"
        verbose_name_plural = "Centros de Resultado"

class AccountPayable(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('OVERDUE', 'Vencido'),
        ('CANCELLED', 'Cancelado'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('BOLETO', 'Boleto'),
        ('PIX', 'Pix'),
        ('CARD', 'Cartão'),
        ('TRANSFER', 'Transferência Bancária'),
        ('CREDIT', 'Crédito'),
    )
    
    description = models.CharField(max_length=255, verbose_name="Descrição")
    supplier = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_supplier': True}, verbose_name="Fornecedor")
    category = models.ForeignKey(FinancialCategory, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'type': 'EXPENSE'}, verbose_name="Categoria")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    due_date = models.DateField(verbose_name="Data de Vencimento")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    
    # Payment details
    occurrence_date = models.DateField(default='2025-01-01', verbose_name="Data de Ocorrência")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True, verbose_name="Forma de Pagamento")
    document_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Documento")
    account = models.ForeignKey(CashAccount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Conta Caixa")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Centro de Resultado")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.description} - {self.amount}"

    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"

class AccountReceivable(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('RECEIVED', 'Recebido'),
        ('OVERDUE', 'Vencido'),
        ('CANCELLED', 'Cancelado'),
    )

    description = models.CharField(max_length=255, verbose_name="Descrição")
    client = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_client': True}, verbose_name="Cliente")
    category = models.ForeignKey(FinancialCategory, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'type': 'REVENUE'}, verbose_name="Categoria")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    due_date = models.DateField(verbose_name="Data de Vencimento")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    invoice = models.ForeignKey('faturamento.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='receivables', verbose_name="Fatura")
    
    # Cora Integration
    cora_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cora ID")
    cora_status = models.CharField(max_length=50, blank=True, null=True, verbose_name="Status Cora")
    cora_copy_paste = models.TextField(blank=True, null=True, verbose_name="Código Pix/Linha Digitável")
    cora_pdf_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL do PDF")

    # Receipt details
    # Receipt details
    occurrence_date = models.DateField(default='2025-01-01', verbose_name="Data de Ocorrência")
    receipt_date = models.DateField(null=True, blank=True, verbose_name="Data de Recebimento")
    payment_method = models.CharField(max_length=50, blank=True, null=True, verbose_name="Forma de Pagamento")
    document_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Documento")
    account = models.ForeignKey(CashAccount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Conta Caixa")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Centro de Resultado")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.description} - {self.amount}"

    class Meta:
        verbose_name = "Conta a Receber"
        verbose_name_plural = "Contas a Receber"

class BankReconciliation(BaseModel):
    date = models.DateField(verbose_name="Data")
    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    TRANSACTION_CHOICES = [
        ('DEBIT', 'Débito'),
        ('CREDIT', 'Crédito'),
    ]
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES, verbose_name="Tipo de Transação")

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} em {self.date}"

    class Meta:
        verbose_name = "Reconciliação Bancária"
        verbose_name_plural = "Reconciliações Bancárias"

class Receipt(BaseModel):
    TYPE_CHOICES = (
        ('PAYMENT', 'Pagamento'),
        ('RECEIPT', 'Recebimento'),
    )
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='RECEIPT', verbose_name="Tipo de Lançamento")
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, verbose_name="Pessoa")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    issue_date = models.DateField(default=timezone.now, verbose_name="Data de Emissão")
    description = models.TextField(verbose_name="Descrição")
    
    def __str__(self):
        return f"Recibo {self.id} - {self.person}"

    class Meta:
        verbose_name = "Recibo"
        verbose_name_plural = "Recibos"

class BudgetPlan(BaseModel):
    year = models.IntegerField(unique=True, verbose_name="Ano")
    description = models.CharField(max_length=255, verbose_name="Descrição")
    
    def __str__(self):
        return f"Planejamento {self.year}"

    class Meta:
        verbose_name = "Planejamento Orçamentário"
        verbose_name_plural = "Planejamentos Orçamentários"

class BudgetItem(BaseModel):
    plan = models.ForeignKey(BudgetPlan, on_delete=models.CASCADE, related_name='items', verbose_name="Planejamento")
    category = models.ForeignKey(FinancialCategory, on_delete=models.CASCADE, verbose_name="Categoria")
    month = models.IntegerField(verbose_name="Mês")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Planejado")
    
    class Meta:
        unique_together = ('plan', 'category', 'month')
        verbose_name = "Item de Orçamento"
        verbose_name_plural = "Itens de Orçamento"
