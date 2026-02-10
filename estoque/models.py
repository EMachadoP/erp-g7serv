from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True

class Brand(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Marca")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

class Category(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome do Grupo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupo de Produto"
        verbose_name_plural = "Grupos de Produtos"

class StockLocation(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome do Local")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Local de Estoque"
        verbose_name_plural = "Locais de Estoque"

class ProductFamily(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Família")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Família de Produto"
        verbose_name_plural = "Famílias de Produtos"

class Product(BaseModel):
    ORIGIN_CHOICES = (
        ('0', '0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8'),
        ('1', '1 - Estrangeira - Importação direta, exceto a indicada no código 6'),
        ('2', '2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7'),
        ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 40% e inferior ou igual a 70%'),
        ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam as legislações citadas nos Ajustes'),
        ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40%'),
        ('6', '6 - Estrangeira - Importação direta, sem similar nacional, constante em lista da CAMEX e gás natural'),
        ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante em lista da CAMEX e gás natural'),
        ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%'),
    )

    name = models.CharField(max_length=255, verbose_name="Nome do Produto")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU / Código")
    internal_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Interno")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marca")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Grupo")
    family = models.ForeignKey(ProductFamily, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Família")
    location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localização")
    
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")
    
    image = models.ImageField(upload_to='produtos/', null=True, blank=True, verbose_name="Imagem do Produto")
    
    # Dados Fiscais
    ncm = models.CharField(max_length=8, blank=True, null=True, verbose_name="NCM")
    cest = models.CharField(max_length=7, blank=True, null=True, verbose_name="CEST")
    product_origin = models.CharField(max_length=1, choices=ORIGIN_CHOICES, default='0', verbose_name="Origem do Produto")
    barcode = models.CharField(max_length=14, blank=True, null=True, verbose_name="Código de Barras")
    supplier_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código do Fornecedor")
    
    # Flags Adicionais
    allow_negative_stock = models.BooleanField(default=True, verbose_name="Permite Estoque Negativo")
    can_be_rented = models.BooleanField(default=True, verbose_name="Pode ser Locado")
    
    minimum_stock = models.IntegerField(default=0, verbose_name="Estoque Mínimo")
    current_stock = models.IntegerField(default=0, verbose_name="Estoque Atual")

    def __str__(self):
        return f"{self.sku} - {self.name}"

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

class StockMovement(BaseModel):
    MOVEMENT_TYPES = (
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name="Produto")
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES, verbose_name="Tipo de Movimentação")
    quantity = models.IntegerField(verbose_name="Quantidade")
    date = models.DateField(auto_now_add=True, verbose_name="Data")
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo")

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"

@receiver(post_save, sender=StockMovement)
def update_stock(sender, instance, created, **kwargs):
    if created:
        if instance.movement_type == 'IN':
            instance.product.current_stock += instance.quantity
        elif instance.movement_type == 'OUT':
            instance.product.current_stock -= instance.quantity
        instance.product.save()

class Inventory(BaseModel):
    STATUS_CHOICES = (
        ('DRAFT', 'Rascunho'),
        ('COMPLETED', 'Concluído'),
    )

    date = models.DateField(verbose_name="Data do Balanço")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Status")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Responsável")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return f"Balanço {self.id} - {self.date}"

    class Meta:
        verbose_name = "Balanço de Estoque"
        verbose_name_plural = "Balanços de Estoque"

class InventoryItem(BaseModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='items', verbose_name="Balanço")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localização")
    system_quantity = models.IntegerField(verbose_name="Qtd. Sistema")
    counted_quantity = models.IntegerField(null=True, blank=True, verbose_name="Qtd. Contada")

    def __str__(self):
        return f"{self.product.name} - {self.inventory}"

    class Meta:
        verbose_name = "Item de Balanço"
        verbose_name_plural = "Itens de Balanço"
