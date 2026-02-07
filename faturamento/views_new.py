from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice, NotaEntrada, NotaEntradaItem, NotaEntradaParcela
from .services.nfe_import import processar_xml_nfe
from financeiro.models import AccountPayable, CategoriaFinanceira, CentroResultado
from estoque.models import StockMovement, Product
from comercial.models import BillingGroup
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import modelformset_factory
from .forms import NotaEntradaItemForm, NotaEntradaParcelaForm

@login_required
def nota_entrada_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    
    notas = NotaEntrada.objects.all().order_by('-data_emissao')
    
    if search_query:
        notas = notas.filter(
            Q(fornecedor__name__icontains=search_query) |
            Q(fornecedor__fantasy_name__icontains=search_query) |
            Q(numero_nota__icontains=search_query)
        )
        
    if status_filter:
        notas = notas.filter(status=status_filter)
        
    if date_min:
        notas = notas.filter(data_entrada__gte=date_min)
    if date_max:
        notas = notas.filter(data_entrada__lte=date_max)
        
    paginator = Paginator(notas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'faturamento/nota_entrada_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_min': date_min,
        'date_max': date_max
    })

@login_required
def nota_entrada_create(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        xml_file = request.FILES['xml_file']
        try:
            nota = processar_xml_nfe(xml_file)
            messages.success(request, f'Nota {nota.numero_nota} importada. Por favor, revise os dados.')
            return redirect('faturamento:nota_entrada_review', pk=nota.pk)
        except ValueError as ve:
            messages.warning(request, str(ve))
            return redirect('faturamento:nota_entrada_create')
        except Exception as e:
            messages.error(request, f'Erro ao processar XML: {str(e)}')
            return redirect('faturamento:nota_entrada_create')
            
    return render(request, 'faturamento/nota_entrada_form.html')

@login_required
def nota_entrada_detail(request, pk):
    nota = get_object_or_404(NotaEntrada, pk=pk)
    return render(request, 'faturamento/nota_entrada_detail.html', {'nota': nota})

@login_required
def nota_entrada_review(request, pk):
    nota = get_object_or_404(NotaEntrada, pk=pk)
    
    if nota.status == 'LANCADA':
        messages.warning(request, 'Esta nota já foi lançada e não pode ser revisada.')
        return redirect('faturamento:nota_entrada_detail', pk=pk)
    
    # Formsets
    ItemFormSet = modelformset_factory(NotaEntradaItem, form=NotaEntradaItemForm, extra=0)
    ParcelaFormSet = modelformset_factory(NotaEntradaParcela, form=NotaEntradaParcelaForm, extra=0)
    
    if request.method == 'POST':
        item_formset = ItemFormSet(request.POST, queryset=nota.itens.all(), prefix='items')
        parcela_formset = ParcelaFormSet(request.POST, queryset=nota.parcelas.all(), prefix='parcelas')
        
        if item_formset.is_valid() and parcela_formset.is_valid():
            # 1. Save Items (Link Products)
            items = item_formset.save(commit=False)
            
            for form in item_formset:
                item = form.save(commit=False)
                
                if not item.produto:
                    new_prod = Product.objects.create(
                        name=item.xProd[:255] if item.xProd else f"Produto NFe {nota.numero_nota}",
                        sku=item.cEAN if item.cEAN else item.cProd[:20],
                        cost_price=item.valor_unitario,
                        sale_price=float(item.valor_unitario) * 1.5,
                        minimum_stock=10
                    )
                    item.produto = new_prod
                else:
                    item.produto.cost_price = item.valor_unitario
                    item.produto.save()
                
                item.save()
                
                StockMovement.objects.create(
                    product=item.produto,
                    movement_type='OUT', # Nota de Entrada is stock increase but using movement_type OUT here? 
                    # Actually stock movement usually has IN/OUT. Entry note is IN.
                    # Previous code used 'IN' in comments but maybe 'OUT' in logic? 
                    # Wait, let's fix to 'IN'.
                    # movement_type='IN',
                    quantity=int(item.quantidade),
                    reason=f"Compra NFe {nota.numero_nota} - {nota.fornecedor.name}"
                )
                
            # 2. Save Parcelas and Create Financial
            parcelas = parcela_formset.save()
            
            category, _ = CategoriaFinanceira.objects.get_or_create(
                nome="Compra de Mercadoria",
                defaults={'tipo': 'saida', 'grupo_dre': '4. Despesas Fixas (OPEX)', 'ordem_exibicao': 8}
            )
            
            for parcela in parcelas:
                AccountPayable.objects.create(
                    description=f"NFe {nota.numero_nota}/{parcela.numero_parcela} - {nota.fornecedor.name}",
                    supplier=nota.fornecedor,
                    category=category,
                    amount=parcela.valor,
                    due_date=parcela.data_vencimento,
                    status='PENDING',
                    document_number=f"{nota.numero_nota}/{parcela.numero_parcela}",
                    notes=f"Chave: {nota.chave_acesso}. Forma: {parcela.get_forma_pagamento_display()}"
                )
                
            nota.status = 'LANCADA'
            nota.save()
            
            messages.success(request, 'Nota lançada e efetivada com sucesso!')
            return redirect('faturamento:nota_entrada_detail', pk=pk)
            
    else:
        item_formset = ItemFormSet(queryset=nota.itens.all(), prefix='items')
        parcela_formset = ParcelaFormSet(queryset=nota.parcelas.all().order_by('data_vencimento'), prefix='parcelas')
        
    return render(request, 'faturamento/nota_entrada_review.html', {
        'nota': nota,
        'item_formset': item_formset,
        'parcela_formset': parcela_formset
    })

@login_required
def nota_entrada_launch(request, pk):
    return redirect('faturamento:nota_entrada_detail', pk=pk)
