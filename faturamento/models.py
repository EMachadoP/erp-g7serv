from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from comercial.models import BillingGroup, Contract
from core.models import Person
from estoque.models import Product


class BillingBatch(models.Model):
    """Representa um lote/processamento de faturamento de contratos."""
    STATUS_CHOICES = [
        ('PROCESSING', 'Em Processamento'),
        ('COMPLETED', 'Concluído'),
        ('ERROR', 'Erro'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Realizado por")
    billing_group = models.ForeignKey(BillingGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Grupo de Faturamento")
    competence_month = models.IntegerField(verbose_name="Mês de Competência")
    competence_year = models.IntegerField(verbose_name="Ano de Competência")
    day_range_start = models.IntegerField(default=1, verbose_name="Dia Cobrança Início")
    day_range_end = models.IntegerField(default=31, verbose_name="Dia Cobrança Fim")
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Iniciado em")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Encerrado em")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING', verbose_name="Status")
    
    # Totalizadores
    total_contracts = models.IntegerField(default=0, verbose_name="Total de Contratos")
    total_invoiced = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Faturado")
    total_not_invoiced = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Não Faturado")
    
    class Meta:
        verbose_name = "Lote de Faturamento"
        verbose_name_plural = "Lotes de Faturamento"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Faturamento {self.competence_month:02d}/{self.competence_year} - {self.get_status_display()}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('PD', 'Pendente'),
        ('PG', 'Paga'),
        ('CN', 'Cancelada'),
    ]

    PAYMENT_METHOD_CHOICES = (
        ('BOLETO', 'Boleto'),
        ('PIX', 'Pix'),
        ('CARD', 'Cartão'),
        ('TRANSFER', 'Transferência Bancária'),
        ('OUTRO', 'Outro'),
    )

    EMAIL_STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ENVIADO', 'Enviado'),
        ('ERRO', 'Erro'),
    ]

    NFSE_STATUS_CHOICES = [
        ('NAO_EMITIDA', 'Não Emitida'),
        ('PROCESSANDO', 'Processando'),
        ('EMITIDA', 'Emitida'),
        ('ERRO', 'Erro'),
        ('CANCELADA', 'Cancelada'),
    ]

    billing_group = models.ForeignKey(BillingGroup, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)
    batch = models.ForeignKey('BillingBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name="Lote de Faturamento")
    client = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='invoices', verbose_name="Cliente", null=True)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name="Contrato")
    competence_month = models.IntegerField(verbose_name="Mês de Competência", null=True)
    competence_year = models.IntegerField(verbose_name="Ano de Competência", null=True)
    
    # Rastreamento de Documentos
    boleto_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL do Boleto")
    nfse_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link da NFSe")
    pdf_fatura = models.FileField(upload_to='faturas/pdf/', blank=True, null=True, verbose_name="PDF da Fatura")
    nfse_record = models.ForeignKey('nfse_nacional.NFSe', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_linked', verbose_name="Registro NFSe Nacional")
    
    # Status de Comunicação
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="E-mail enviado em")
    email_status = models.CharField(max_length=15, choices=EMAIL_STATUS_CHOICES, default='PENDENTE', verbose_name="Status do E-mail")
    nfse_status = models.CharField(max_length=15, choices=NFSE_STATUS_CHOICES, default='NAO_EMITIDA', verbose_name="Status da NFSe")
    
    number = models.CharField(max_length=30, unique=True, blank=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='PD')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='BOLETO', verbose_name="Forma de Pagamento")
    complementary_info = models.TextField(blank=True, null=True, verbose_name="Informações Complementares")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fatura {self.number}"

    def save(self, *args, **kwargs):
        if not self.number:
            # Get the last invoice number to determine the sequence
            # We filter for numbers starting with 'FAT-' to maintain the sequence correctly
            last_invoice = Invoice.objects.filter(number__startswith='FAT-').order_by('id').last()
            if not last_invoice:
                self.number = 'FAT-0001'
            else:
                try:
                    # Try to extract the numeric part
                    last_number_str = last_invoice.number.split('-')[1]
                    next_number = int(last_number_str) + 1
                    self.number = f'FAT-{next_number:04d}'
                except (IndexError, ValueError):
                    # Fallback to ID-based if parsing fails
                    next_id = (Invoice.objects.all().order_by('id').last().id or 0) + 1
                    self.number = f'FAT-{next_id:04d}'
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('SERVICE', 'Serviço'),
        ('PRODUCT', 'Produto'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name="Fatura")
    financial_category = models.ForeignKey('financeiro.CategoriaFinanceira', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria Financeira (DRE)")
    description = models.CharField(max_length=255, verbose_name="Descrição/Produto/Serviço")
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='SERVICE', verbose_name="Tipo")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Preço Unitário")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Preço Total")
    
    notes = models.TextField(blank=True, null=True, verbose_name="Observações/Referência")

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.invoice.number})"

    class Meta:
        verbose_name = "Item da Fatura"
        verbose_name_plural = "Itens da Fatura"

class NotaEntrada(models.Model):
    STATUS_CHOICES = [
        ('IMPORTADA', 'Importada'),
        ('LANCADA', 'Lançada'),
        ('CANCELADA', 'Cancelada'),
    ]

    fornecedor = models.ForeignKey(Person, on_delete=models.PROTECT, limit_choices_to={'is_supplier': True}, verbose_name="Fornecedor")
    chave_acesso = models.CharField(max_length=44, verbose_name="Chave de Acesso", unique=True)
    numero_nota = models.CharField(max_length=20, verbose_name="Número da Nota")
    serie = models.CharField(max_length=5, verbose_name="Série")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_entrada = models.DateField(default=timezone.now, verbose_name="Data de Entrada")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    arquivo_xml = models.FileField(upload_to='uploads/nfe/', verbose_name="Arquivo XML")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IMPORTADA', verbose_name="Status")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NFe {self.numero_nota} - {self.fornecedor.fantasy_name or self.fornecedor.name}"

    class Meta:
        verbose_name = "Nota Fiscal de Entrada"
        verbose_name_plural = "Notas Fiscais de Entrada"

class NotaEntradaItem(models.Model):
    nota = models.ForeignKey(NotaEntrada, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Produto", null=True, blank=True)
    quantidade = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Quantidade")
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="Valor Unitário")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    cfop = models.CharField(max_length=4, verbose_name="CFOP")
    
    # Original XML Data for De/Para
    xProd = models.CharField(max_length=255, verbose_name="Nome no XML", blank=True, null=True)
    cProd = models.CharField(max_length=60, verbose_name="Código no XML", blank=True, null=True)
    cEAN = models.CharField(max_length=14, verbose_name="EAN no XML", blank=True, null=True)
    
    def __str__(self):
        return f"{self.produto.name} - {self.quantidade}"

class NotaEntradaParcela(models.Model):
    nota = models.ForeignKey(NotaEntrada, on_delete=models.CASCADE, related_name='parcelas')
    numero_parcela = models.CharField(max_length=3, verbose_name="Nº Parcela")
    data_vencimento = models.DateField(verbose_name="Vencimento")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    
    PAYMENT_FORMS = [
        ('DINHEIRO', 'Dinheiro'),
        ('BOLETO', 'Boleto Bancário'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('TRANSFERENCIA', 'Transferência'),
        ('OUTROS', 'Outros'),
    ]
    forma_pagamento = models.CharField(max_length=20, choices=PAYMENT_FORMS, default='BOLETO', verbose_name="Forma de Pagamento")

    def __str__(self):
        return f"Parcela {self.numero_parcela} - {self.nota}"
