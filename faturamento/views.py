from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice, NotaEntrada, NotaEntradaItem, NotaEntradaParcela
from .forms import InvoiceForm, NotaEntradaItemForm, NotaEntradaParcelaForm
from .services.nfe_import import processar_xml_nfe
from financeiro.models import AccountPayable, FinancialCategory, CostCenter
from estoque.models import StockMovement, Product
from comercial.models import BillingGroup
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def invoice_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    invoices = Invoice.objects.select_related('billing_group').all().order_by('-issue_date')
    
    if search_query:
        invoices = invoices.filter(
            Q(number__icontains=search_query) |
            Q(billing_group__name__icontains=search_query)
        )
        
    if status_filter:
        invoices = invoices.filter(status=status_filter)
        
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'faturamento/invoice_list.html', {
        'page_obj': page_obj, 
        'search_query': search_query,
        'status_filter': status_filter
    })

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'faturamento/invoice_detail.html', {'invoice': invoice})

@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, 'Fatura criada com sucesso.')
            return redirect('faturamento:detail', pk=invoice.id)
    else:
        form = InvoiceForm()
    
    return render(request, 'faturamento/invoice_form.html', {'form': form})

@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fatura atualizada com sucesso.')
            return redirect('faturamento:detail', pk=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)
        
    return render(request, 'faturamento/invoice_form.html', {'invoice': invoice, 'form': form})

from operacional.models import ServiceOrder
from comercial.models import Contract
from django.utils import timezone
from datetime import timedelta

@login_required
def create_invoice_from_os(request, os_id):
    os = get_object_or_404(ServiceOrder, pk=os_id)
    
    # Check if invoice already exists (optional logic, skipping for now)
    
    # Create a default Billing Group if none exists
    billing_group, created = BillingGroup.objects.get_or_create(name="Padrão")
    
    invoice = Invoice.objects.create(
        billing_group=billing_group,
        number=f"OS-{os.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
        issue_date=timezone.now(),
        due_date=timezone.now() + timedelta(days=15),
        amount=os.value,
        status='PD'
    )
    
    messages.success(request, f'Fatura criada com sucesso a partir da OS #{os.id}')
    return redirect('faturamento:update', pk=invoice.id)

@login_required
def create_invoice_from_contract(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    
    billing_group, created = BillingGroup.objects.get_or_create(name="Contratos")
    
    invoice = Invoice.objects.create(
        billing_group=billing_group,
        number=f"CTR-{contract.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
        issue_date=timezone.now(),
        due_date=timezone.now() + timedelta(days=30),
        amount=contract.value,
        status='PD'
    )
    
    messages.success(request, f'Fatura criada com sucesso a partir do Contrato #{contract.id}')
    return redirect('faturamento:update', pk=invoice.id)

# Contract Billing Views
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from financeiro.models import AccountReceivable, FinancialCategory
from financeiro.services.email_service import BillingEmailService
from financeiro.integrations.cora import CoraAPI
from datetime import date
import json

@login_required
def contract_billing_view(request):
    billing_groups = BillingGroup.objects.filter(active=True)
    current_year = timezone.now().year
    return render(request, 'faturamento/contract_billing.html', {
        'billing_groups': billing_groups,
        'current_year': current_year
    })

@login_required
def search_contracts(request):
    month = int(request.GET.get('month'))
    year = int(request.GET.get('year'))
    group_id = request.GET.get('group')
    
    contracts = Contract.objects.filter(status='Ativo')
    
    if group_id:
        contracts = contracts.filter(billing_group_id=group_id)
        
    # Exclude contracts already billed for this competence
    billed_contract_ids = Invoice.objects.filter(
        competence_month=month,
        competence_year=year,
        contract__isnull=False
    ).values_list('contract_id', flat=True)
    
    contracts = contracts.exclude(id__in=billed_contract_ids)
    
    data = []
    for contract in contracts:
        data.append({
            'id': contract.id,
            'client_name': contract.client.name,
            'group_name': contract.billing_group.name if contract.billing_group else None,
            'due_day': contract.due_day,
            'value': str(contract.value)
        })
        
    return JsonResponse({'contracts': data})

@login_required
@require_POST
def process_contract_billing(request):
    month = int(request.POST.get('competence_month'))
    year = int(request.POST.get('competence_year'))
    contract_ids = request.POST.getlist('selected_contracts')
    
    if not contract_ids:
        messages.error(request, 'Nenhum contrato selecionado.')
        return redirect('faturamento:contract_billing')
        
    contracts = Contract.objects.filter(id__in=contract_ids)
    created_count = 0
    email_count = 0
    
    # Get or create default category for contracts
    category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Contratos",
        defaults={'type': 'REVENUE'}
    )
    
    cora = CoraAPI()
    
    for contract in contracts:
        # Double check if already billed
        if Invoice.objects.filter(contract=contract, competence_month=month, competence_year=year).exists():
            continue
            
        try:
            with transaction.atomic():
                # Calculate due date
                try:
                    due_date = date(year, month, contract.due_day)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    due_date = date(year, month, last_day)
                
                # 1. Create Invoice
                invoice = Invoice.objects.create(
                    client=contract.client,
                    contract=contract,
                    billing_group=contract.billing_group,
                    competence_month=month,
                    competence_year=year,
                    number=f"CTR-{contract.id}-{year}{month:02d}",
                    issue_date=timezone.now(),
                    due_date=due_date,
                    amount=contract.value,
                    status='PD'
                )
                
                # 2. Integrate with Cora (Passo 4)
                boleto_url = cora.gerar_boleto(invoice)
                if boleto_url:
                    invoice.boleto_url = boleto_url
                    invoice.save()
                
                # 3. Create Account Receivable
                AccountReceivable.objects.create(
                    description=f"Fatura Contrato #{contract.id} - {month}/{year}",
                    client=contract.client,
                    category=category,
                    amount=contract.value,
                    due_date=due_date,
                    status='PENDING',
                    invoice=invoice,
                    document_number=invoice.number
                )
                
                created_count += 1
                
                # 4. Send Email (Passo 2)
                if BillingEmailService.send_invoice_email(invoice):
                    invoice.email_sent_at = timezone.now()
                    invoice.save()
                    email_count += 1
                    
        except Exception as e:
            messages.error(request, f"Erro ao processar contrato #{contract.id}: {str(e)}")
            continue
            
    # Handle HTMX request (Passo 3: hx-post)
    if request.headers.get('HX-Request'):
        return render(request, 'faturamento/partials/billing_result_message.html', {
            'created_count': created_count,
            'email_count': email_count
        })
        
    messages.success(request, f'{created_count} faturas geradas ({email_count} e-mails enviados).')
    return redirect('faturamento:contract_billing_summary')

@login_required
def contract_billing_summary(request):
    # Show recent invoices (e.g., last 50)
    invoices = Invoice.objects.filter(contract__isnull=False).order_by('-created_at')[:50]
    return render(request, 'faturamento/contract_billing_summary.html', {'invoices': invoices})

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

from django.forms import modelformset_factory
from .forms import NotaEntradaItemForm, NotaEntradaParcelaForm

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
            # 1. Save Items (Link Products) AND Update Models
            # Iterate formset to handle custom logic per item
            items_instances = item_formset.save(commit=False) # Get instances but don't save to DB yet if generic. 
            # Actually we can save(commit=False), inspect, then save.
            
            for form in item_formset:
                item = form.save(commit=False)
                
                # Check validation (already done by is_valid but let's be safe)
                
                if not item.produto:
                    # Create New Product Logic
                    new_prod = Product.objects.create(
                        name=item.xProd[:255] if item.xProd else f"Produto NFe {nota.numero_nota}",
                        sku=item.cEAN if item.cEAN else item.cProd[:20],
                        cost_price=item.valor_unitario,
                        sale_price=float(item.valor_unitario) * 1.5,
                        minimum_stock=10
                    )
                    item.produto = new_prod
                else:
                    # Update cost
                    item.produto.cost_price = item.valor_unitario
                    item.produto.save()
                
                item.save()
                
                # Stock Movement
                StockMovement.objects.create(
                    product=item.produto,
                    movement_type='IN',
                    quantity=int(item.quantidade),
                    reason=f"Compra NFe {nota.numero_nota} - {nota.fornecedor.name}"
                )
                
            # 2. Save Parcelas and Create Financial
            parcelas = parcela_formset.save()
            
            category, _ = FinancialCategory.objects.get_or_create(
                name="Compra de Mercadoria",
                defaults={'type': 'EXPENSE'}
            )
            
            total_parcelas = len(parcelas)
            for i, parcela in enumerate(parcelas):
                parcela_str = f"{i+1}/{total_parcelas}"
                AccountPayable.objects.create(
                    description=f"NFe {nota.numero_nota} ({parcela_str}) - {nota.fornecedor.name}",
                    supplier=nota.fornecedor,
                    category=category,
                    amount=parcela.valor,
                    due_date=parcela.data_vencimento,
                    status='PENDING',
                    document_number=f"{nota.numero_nota}/{parcela.numero_parcela}", # Keep original doc num
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

from django.db import transaction

@login_required
@transaction.atomic
def nota_entrada_revert(request, pk):
    nota = get_object_or_404(NotaEntrada, pk=pk)
    
    if nota.status != 'LANCADA':
        messages.warning(request, 'Apenas notas lançadas podem ser estornadas.')
        return redirect('faturamento:nota_entrada_detail', pk=pk)
        
    # Check if any linked AccountPayable is PAID
    # Linking by 'notes' contains the key is our current method
    linked_payables = AccountPayable.objects.filter(notes__icontains=nota.chave_acesso)
    if linked_payables.filter(status='PAID').exists():
        messages.error(request, 'Não é possível estornar nota com parcelas já pagas. Estorne o pagamento primeiro.')
        return redirect('faturamento:nota_entrada_detail', pk=pk)
        
    # 1. Reverse Financial (Delete AccountPayable)
    deleted_count, _ = linked_payables.delete()
    
    # 2. Reverse Stock (Create OUT movements)
    for item in nota.itens.all():
        if item.produto:
            StockMovement.objects.create(
                product=item.produto,
                movement_type='OUT',
                quantity=int(item.quantidade),
                reason=f"Estorno NFe {nota.numero_nota} - {nota.fornecedor.name}"
            )
            
    # 3. Update Status
    # Returning to 'IMPORTADA' allows re-review and re-launch (Correction Flow)
    nota.status = 'IMPORTADA'
    nota.save()
    
    messages.success(request, f'Nota estornada com sucesso! Status revertido para Importada. {deleted_count} registros financeiros removidos.')
    return redirect('faturamento:nota_entrada_list')

@login_required
def nota_entrada_delete(request, pk):
    nota = get_object_or_404(NotaEntrada, pk=pk)
    
    if nota.status == 'LANCADA':
        messages.error(request, 'Não é possível excluir uma nota lançada. Estorne-a primeiro.')
        return redirect('faturamento:nota_entrada_detail', pk=pk)
        
    nota.delete()
    messages.success(request, 'Nota fiscal excluída com sucesso.')
    return redirect('faturamento:nota_entrada_list')
