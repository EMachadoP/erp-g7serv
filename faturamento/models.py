from django.db import models
from django.utils import timezone
from comercial.models import BillingGroup, Contract
from core.models import Person
from estoque.models import Product

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('PD', 'Pendente'),
        ('PG', 'Paga'),
        ('CN', 'Cancelada'),
    ]

    billing_group = models.ForeignKey(BillingGroup, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)
    client = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='invoices', verbose_name="Cliente", null=True)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name="Contrato")
    competence_month = models.IntegerField(verbose_name="Mês de Competência", null=True)
    competence_year = models.IntegerField(verbose_name="Ano de Competência", null=True)
    
    number = models.CharField(max_length=30, unique=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='PD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fatura {self.number}"

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
