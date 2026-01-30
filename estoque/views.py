from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProductForm

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Produto criado com sucesso.')
            return redirect('estoque:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'estoque/product_form.html', {'form': form, 'title': 'Novo Produto'})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso.')
            return redirect('estoque:product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'estoque/product_form.html', {'form': form, 'title': 'Editar Produto'})

from django.contrib import messages
from .models import Product, StockMovement, Brand, Category, StockLocation, Inventory, InventoryItem
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def product_list(request):
    search_query = request.GET.get('search', '')
    
    products = Product.objects.all().order_by('name')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
        
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'estoque/product_list.html', {'page_obj': page_obj, 'search_query': search_query})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.movements.all().order_by('-date', '-created_at')[:10]
    return render(request, 'estoque/product_detail.html', {'product': product, 'movements': movements})

@login_required
def movement_list(request):
    movements = StockMovement.objects.all().order_by('-date', '-created_at')
    return render(request, 'estoque/movement_list.html', {'movements': movements})

@login_required
def movement_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        movement_type = request.POST.get('movement_type')
        quantity = int(request.POST.get('quantity'))
        reason = request.POST.get('reason')
        
        product = get_object_or_404(Product, pk=product_id)
        
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason
        )
        
        messages.success(request, 'Movimentação registrada com sucesso.')
        return redirect('estoque:product_detail', pk=product.id)
        
    products = Product.objects.filter(active=True)
    return render(request, 'estoque/movement_form.html', {'products': products})

@login_required
def brand_list(request):
    brands = Brand.objects.filter(active=True).order_by('name')
    return render(request, 'estoque/brand_list.html', {'brands': brands})

@login_required
def brand_create(request):
    if request.method == 'POST':
        Brand.objects.create(name=request.POST.get('name'))
        messages.success(request, 'Marca criada com sucesso.')
        return redirect('estoque:brand_list')
    return render(request, 'estoque/brand_form.html')

@login_required
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.name = request.POST.get('name')
        brand.save()
        messages.success(request, 'Marca atualizada com sucesso.')
        return redirect('estoque:brand_list')
    return render(request, 'estoque/brand_form.html', {'brand': brand})

@login_required
def category_list(request):
    categories = Category.objects.filter(active=True).order_by('name')
    return render(request, 'estoque/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        Category.objects.create(name=request.POST.get('name'))
        messages.success(request, 'Grupo de Produto criado com sucesso.')
        return redirect('estoque:category_list')
    return render(request, 'estoque/category_form.html')

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        messages.success(request, 'Grupo de Produto atualizado com sucesso.')
        return redirect('estoque:category_list')
    return render(request, 'estoque/category_form.html', {'category': category})

@login_required
def location_list(request):
    locations = StockLocation.objects.filter(active=True).order_by('name')
    return render(request, 'estoque/location_list.html', {'locations': locations})

@login_required
def location_create(request):
    if request.method == 'POST':
        StockLocation.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        messages.success(request, 'Local de Estoque criado com sucesso.')
        return redirect('estoque:location_list')
    return render(request, 'estoque/location_form.html')

@login_required
def location_update(request, pk):
    location = get_object_or_404(StockLocation, pk=pk)
    if request.method == 'POST':
        location.name = request.POST.get('name')
        location.description = request.POST.get('description')
        location.save()
        messages.success(request, 'Local de Estoque atualizado com sucesso.')
        return redirect('estoque:location_list')
    return render(request, 'estoque/location_form.html', {'location': location})

@login_required
def inventory_list(request):
    inventories = Inventory.objects.all().order_by('-date', '-created_at')
    return render(request, 'estoque/inventory_list.html', {'inventories': inventories})

@login_required
def inventory_create(request):
    if request.method == 'POST':
        inventory = Inventory.objects.create(
            date=request.POST.get('date'),
            description=request.POST.get('description'),
            created_by=request.user
        )
        
        # Populate with all active products
        products = Product.objects.filter(active=True)
        for product in products:
            InventoryItem.objects.create(
                inventory=inventory,
                product=product,
                location=product.location,
                system_quantity=product.current_stock
            )
            
        messages.success(request, 'Balanço de Estoque iniciado com sucesso.')
        return redirect('estoque:inventory_detail', pk=inventory.id)
    return render(request, 'estoque/inventory_form.html')

@login_required
def inventory_detail(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)
    items = inventory.items.all().select_related('product', 'location').order_by('product__name')
    
    if request.method == 'POST':
        if 'finish_inventory' in request.POST:
            inventory.status = 'COMPLETED'
            inventory.save()
            
            # Update stock based on counts? 
            # For now, just mark as completed. 
            # Ideally we would create StockMovements to adjust stock.
            # Let's implement stock adjustment logic here.
            for item in items:
                if item.counted_quantity is not None:
                    diff = item.counted_quantity - item.system_quantity
                    if diff != 0:
                        StockMovement.objects.create(
                            product=item.product,
                            movement_type='IN' if diff > 0 else 'OUT',
                            quantity=abs(diff),
                            reason=f'Ajuste de Balanço #{inventory.id}'
                        )
            
            messages.success(request, 'Balanço concluído e estoque ajustado.')
            return redirect('estoque:inventory_list')
            
        else:
            # Saving counts
            for item in items:
                count_key = f'count_{item.id}'
                if count_key in request.POST:
                    try:
                        count_val = request.POST.get(count_key)
                        if count_val:
                            item.counted_quantity = int(count_val)
                            item.save()
                    except ValueError:
                        pass
            messages.success(request, 'Contagens salvas com sucesso.')
            return redirect('estoque:inventory_detail', pk=inventory.id)
            
    return render(request, 'estoque/inventory_detail.html', {'inventory': inventory, 'items': items})
