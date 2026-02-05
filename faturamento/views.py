from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice, NotaEntrada, NotaEntradaItem, NotaEntradaParcela, BillingBatch, InvoiceItem
from .forms import InvoiceForm, NotaEntradaItemForm, NotaEntradaParcelaForm, InvoiceItemFormSet
from .services.nfe_import import processar_xml_nfe
from financeiro.models import AccountPayable, FinancialCategory, CostCenter
from estoque.models import StockMovement, Product
from comercial.models import BillingGroup
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import transaction
from decimal import Decimal

@login_required
def invoice_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    month_filter = request.GET.get('month', '')
    year_filter = request.GET.get('year', '')
    
    invoices = Invoice.objects.select_related('client', 'billing_group').all().order_by('-id')
    
    if search_query:
        invoices = invoices.filter(
            Q(number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(billing_group__name__icontains=search_query)
        )
        
    if status_filter:
        invoices = invoices.filter(status=status_filter)
        
    if month_filter:
        invoices = invoices.filter(competence_month=month_filter)
        
    if year_filter:
        invoices = invoices.filter(competence_year=year_filter)
        
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepara lista de anos com selected pré-calculado
    years_raw = Invoice.objects.values_list('competence_year', flat=True).distinct().order_by('-competence_year')
    years = [{'value': str(y), 'label': str(y), 'selected': str(y) == year_filter} for y in years_raw]
    
    # Prepara lista de meses com selected pré-calculado
    months_raw = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    months = [{'value': str(m[0]), 'label': m[1], 'selected': str(m[0]) == month_filter} for m in months_raw]
    
    # Prepara lista de status com selected pré-calculado
    statuses = [
        {'value': 'PD', 'label': 'Pendente', 'selected': status_filter == 'PD'},
        {'value': 'PG', 'label': 'Paga', 'selected': status_filter == 'PG'},
        {'value': 'CN', 'label': 'Cancelada', 'selected': status_filter == 'CN'},
    ]
    
    # Email templates para ações em massa
    from core.models import EmailTemplate
    email_templates = EmailTemplate.objects.filter(active=True)
    
    return render(request, 'faturamento/invoice_list_v5.html', {
        'page_obj': page_obj, 
        'search_query': search_query,
        'status_filter': status_filter,
        'month_filter': month_filter,
        'year_filter': year_filter,
        'years': years,
        'months': months,
        'statuses': statuses,
        'email_templates': email_templates,
    })

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'faturamento/invoice_detail.html', {'invoice': invoice})

@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save()
                formset.instance = invoice
                formset.save()
                
                # Recalculate amount if items exist
                if invoice.items.exists():
                    total_amount = sum(item.total_price for item in invoice.items.all())
                    invoice.amount = total_amount
                    invoice.save()
                    
                messages.success(request, 'Fatura criada com sucesso.')
                return redirect('faturamento:detail', pk=invoice.id)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet(prefix='items')
    
    return render(request, 'faturamento/invoice_form.html', {'form': form, 'formset': formset})


@login_required
def invoice_standalone_create(request):
    """Cria fatura avulsa sem vínculo de contrato"""
    from .forms import StandaloneInvoiceForm
    
    if request.method == 'POST':
        form = StandaloneInvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.contract = None
                invoice.save()
                
                formset.instance = invoice
                formset.save()
                
                # Recalculate amount from items
                if invoice.items.exists():
                    invoice.amount = sum(item.total_price for item in invoice.items.all())
                    invoice.save()
                
                messages.success(request, 'Fatura avulsa criada com sucesso.')
                return redirect('faturamento:detail', pk=invoice.id)
    else:
        form = StandaloneInvoiceForm()
        formset = InvoiceItemFormSet(prefix='items')

    return render(request, 'faturamento/invoice_standalone_form.html', {'form': form, 'formset': formset})

@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix='items')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                
                # Recalculate amount from items if present
                if invoice.items.exists():
                    invoice.amount = sum(item.total_price for item in invoice.items.all())
                    invoice.save()
                    
                messages.success(request, 'Fatura atualizada com sucesso.')
                return redirect('faturamento:detail', pk=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix='items')
        
    return render(request, 'faturamento/invoice_form.html', {
        'invoice': invoice, 
        'form': form, 
        'formset': formset
    })

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
from financeiro.integrations.cora import CoraService
from faturamento.services.invoice_service import generate_invoice_pdf_file
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
    group_id = request.POST.get('billing_group')
    day_start = int(request.POST.get('day_range_start', 1))
    day_end = int(request.POST.get('day_range_end', 31))
    
    if not contract_ids:
        messages.error(request, 'Nenhum contrato selecionado.')
        return redirect('faturamento:contract_billing')
    
    # Get billing group if specified
    billing_group = None
    if group_id:
        billing_group = BillingGroup.objects.filter(id=group_id).first()
    
    # Create BillingBatch to track this processing
    batch = BillingBatch.objects.create(
        user=request.user,
        billing_group=billing_group,
        competence_month=month,
        competence_year=year,
        day_range_start=day_start,
        day_range_end=day_end,
        total_contracts=len(contract_ids)
    )
        
    contracts = Contract.objects.filter(id__in=contract_ids)
    created_count = 0
    email_count = 0
    total_invoiced = Decimal('0.00')
    
    # Get or create default category for contracts
    category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Contratos",
        defaults={'type': 'REVENUE'}
    )
    
    cora = CoraService()
    
    for contract in contracts:
        # Double check if already billed
        if Invoice.objects.filter(contract=contract, competence_month=month, competence_year=year).exists():
            continue
            
        try:
            with transaction.atomic():
                # Calculate due date: Priority 1: Billing Group, Priority 2: Contract
                due_day = contract.due_day
                if contract.billing_group and contract.billing_group.due_day:
                    due_day = contract.billing_group.due_day
                
                try:
                    due_date = date(year, month, due_day)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    due_date = date(year, month, last_day)
                
                # Issue date is today
                issue_date = timezone.now().date()
                
                # 1. Create Invoice linked to batch
                invoice = Invoice.objects.create(
                    client=contract.client,
                    contract=contract,
                    batch=batch,
                    billing_group=contract.billing_group,
                    competence_month=month,
                    competence_year=year,
                    issue_date=issue_date,
                    due_date=due_date,
                    amount=contract.value,
                    status='PD'
                )

                # 1.1 Create InvoiceItems from Contract items if they exist
                contract_items = contract.items.all()
                if contract_items.exists():
                    for item in contract_items:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            item_type='SERVICE' if item.category != 'COMODATO' else 'RENT',
                            description=item.description,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            total_price=item.total_price,
                            notes=f"Categoria: {item.get_category_display()}"
                        )
                else:
                    # Fallback for old single-value contracts
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type='SERVICE',
                        description=f"Serviços de {contract.billing_group.name if contract.billing_group else 'Suporte'}",
                        quantity=1,
                        unit_price=contract.value,
                        total_price=contract.value,
                        notes=f"Competência: {month:02d}/{year}"
                    )
                
                # 2. Integrate with Cora v2 (mTLS)
                fatura_data = {
                    "customer": {
                        "name": contract.client.name,
                        "email": contract.client.email or "faturamento@g7serv.com.br",
                        "document": {
                            "identity": contract.client.document or "00000000000",
                            "type": "CNPJ" if len(contract.client.document or "") > 11 else "CPF"
                        }
                    },
                    "payment_methods": ["BANK_SLIP", "PIX"],
                    "services": [
                        {
                            "name": f"Serviços de {contract.billing_group.name if contract.billing_group else 'Suporte'}",
                            "description": f"Competência: {month:02d}/{year}",
                            "amount": int(invoice.amount * 100),
                            "quantity": 1
                        }
                    ],
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "post_notifications": False # Tenta silenciar e-mail automático da Cora
                }
                
                try:
                    cora_response = cora.gerar_fatura(fatura_data)
                    if "payment_url" in cora_response:
                        invoice.boleto_url = cora_response["payment_url"]
                        invoice.save()
                    elif "id" in cora_response:
                        invoice.boleto_url = cora_response.get("url") or cora_response.get("payment_url")
                        invoice.save()
                except Exception:
                    pass  # Continue even if Cora fails

                # 3. Create Account Receivable
                AccountReceivable.objects.create(
                    description=f"Fatura Contrato #{contract.id} - {month}/{year}",
                    client=contract.client,
                    category=category,
                    amount=contract.value,
                    due_date=due_date,
                    status='PENDING',
                    document_number=invoice.number,
                    invoice=invoice # Link important for cancellation
                )
                
                # 3.1 Gerar PDF da Fatura (Demonstrativo)
                generate_invoice_pdf_file(invoice)
                
                created_count += 1
                total_invoiced += contract.value
                
                # 4. Send Email (optional - don't fail if email fails)
                try:
                    if BillingEmailService.send_invoice_email(invoice):
                        invoice.email_sent_at = timezone.now()
                        invoice.save()
                        email_count += 1
                except Exception:
                    pass
                    
        except Exception as e:
            messages.error(request, f"Erro ao processar contrato #{contract.id}: {str(e)}")
            continue

@login_required
def invoice_cancel(request, pk):
    """Cancela a fatura e o contas a receber vinculado."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'PG':
        messages.error(request, 'Não é possível cancelar uma fatura que já está paga.')
        return redirect('faturamento:detail', pk=pk)
        
    try:
        with transaction.atomic():
            # 1. Update Invoice status
            invoice.status = 'CN'
            invoice.save(update_fields=['status'])
            
            # 2. Update all linked Receivables
            receivables = AccountReceivable.objects.filter(invoice=invoice)
            for rec in receivables:
                if rec.status != 'RECEIVED':
                    rec.status = 'CANCELLED'
                    rec.save(update_fields=['status'])
            
            messages.success(request, f'Fatura #{invoice.number} cancelada com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao cancelar fatura: {str(e)}')
        
    return redirect('faturamento:list')
    
    # Update batch with final stats
    batch.finished_at = timezone.now()
    batch.status = 'COMPLETED'
    batch.total_invoiced = total_invoiced
    batch.save()
            
    # Handle HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'faturamento/partials/billing_result_message.html', {
            'created_count': created_count,
            'email_count': email_count,
            'batch': batch
        })
        
    messages.success(request, f'{created_count} faturas geradas ({email_count} e-mails enviados).')
    return redirect('faturamento:billing_batch_detail', pk=batch.pk)


@login_required
def contract_billing_summary(request):
    """Lista de todos os lotes de faturamento."""
    batches = BillingBatch.objects.all().order_by('-started_at')[:50]
    return render(request, 'faturamento/contract_billing_summary.html', {'batches': batches})


@login_required
def billing_batch_detail(request, pk):
    """Detalhes de um lote de faturamento específico."""
    batch = get_object_or_404(BillingBatch, pk=pk)
    
    # Buscar faturas do lote com filtros
    search_query = request.GET.get('search', '')
    invoices = batch.invoices.select_related('client', 'contract').all()
    
    if search_query:
        invoices = invoices.filter(
            Q(number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(contract__id__icontains=search_query)
        )
    
    # Calcular totalizadores
    totals = invoices.aggregate(
        total_faturado=Sum('amount')
    )
    
    # Paginação
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Templates de email disponíveis
    from core.models import EmailTemplate
    email_templates = EmailTemplate.objects.filter(active=True)
    
    context = {
        'batch': batch,
        'page_obj': page_obj,
        'invoices': page_obj,
        'search_query': search_query,
        'total_faturado': totals['total_faturado'] or Decimal('0.00'),
        'email_templates': email_templates,
    }
    return render(request, 'faturamento/billing_batch_detail.html', context)


# ==============================================================================
# Ações em Massa para Faturas
# ==============================================================================

@login_required
@require_POST
def invoice_bulk_generate_boletos(request):
    """Gera boletos em lote para faturas selecionadas."""
    import json
    from integracao_cora.services.boleto import CoraBoleto
    from integracao_cora.models import CoraConfig
    
    invoice_ids = request.POST.getlist('invoice_ids[]')
    if not invoice_ids:
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            force_regenerate = data.get('force', False)
        except:
            force_regenerate = False
    
    if not invoice_ids:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma fatura selecionada.'}, status=400)
    
    # Permite regenerar boletos - não filtra por boleto_url__isnull
    invoices = Invoice.objects.filter(id__in=invoice_ids)
    
    # Verificar se Cora está configurada
    config = CoraConfig.objects.first()
    if not config:
        return JsonResponse({
            'status': 'error', 
            'message': 'Integração Cora não configurada. Acesse Integrações > Cora para configurar.'
        }, status=400)
    
    success_count = 0
    skipped_count = 0
    errors = []
    
    from integracao_cora.services.base import mTLS_cert_paths
    
    with mTLS_cert_paths() as certs:
        for invoice in invoices:
            try:
                # Se já tem boleto e não forçou regeneração, pula
                if invoice.boleto_url and not invoice.boleto_url.startswith('https://www.cora.com.br/boleto/simulado'):
                    skipped_count += 1
                    continue
                    
                # Prepara dados do cliente
                if not invoice.client:
                    errors.append(f"Fatura #{invoice.number}: Cliente não informado")
                    continue
                    
                customer_document = (invoice.client.document or "").replace('.', '').replace('-', '').replace('/', '')
                if not customer_document:
                    errors.append(f"Fatura #{invoice.number}: CPF/CNPJ do cliente não informado")
                    continue
                
                # Verificar valor mínimo exigido pela Cora (R$ 5,00)
                if invoice.amount < Decimal('5.00'):
                    errors.append(f"Fatura #{invoice.number}: Valor R$ {invoice.amount} é inferior ao mínimo de R$ 5,00 para boletos.")
                    continue

                # Instancia serviço de boleto Cora
                cora = CoraBoleto()
                
                # Cria objeto que simula NFSe para compatibilidade com CoraBoleto
                class FaturaWrapper:
                    def __init__(self, inv):
                        self.original_invoice = inv
                        self.numero_dps = inv.number
                        self.cliente = inv.client
                        self.due_date = inv.due_date
                        self.servico = type('obj', (object,), {
                            'name': f'Fatura {inv.number}',
                            'sale_price': inv.amount
                        })()
                
                print(f"[DEBUG] Gerando boleto para fatura {invoice.number}")
                
                boleto = cora.gerar_boleto(FaturaWrapper(invoice), cert_files=certs)
            
                if boleto and boleto.url_pdf:
                    invoice.boleto_url = boleto.url_pdf
                    invoice.save()
                    
                    # Atualiza também o Contas a Receber se existir
                    from financeiro.models import AccountReceivable
                    receivable = AccountReceivable.objects.filter(invoice=invoice).first()
                    if receivable:
                        receivable.cora_id = boleto.cora_id
                        receivable.cora_pdf_url = boleto.url_pdf
                        receivable.cora_status = 'Aberto'
                        receivable.save()

                    success_count += 1
                else:
                    errors.append(f"Fatura #{invoice.number}: Boleto gerado mas sem URL")
                
            except Exception as e:
                errors.append(f"Fatura #{invoice.number}: {str(e)}")
    
    message = f'{success_count} boleto(s) gerado(s) com sucesso.'
    if skipped_count > 0:
        message += f' {skipped_count} já possuíam boleto.'
    if errors:
        message += f' {len(errors)} erro(s).'
    
    return JsonResponse({
        'status': 'success' if success_count > 0 else 'warning',
        'message': message,
        'success_count': success_count,
        'errors': errors
    })


@login_required
def invoice_cancel_boleto(request, pk):
    """Cancela o boleto da fatura (limpa a URL)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'PG':
        messages.error(request, "Não é possível cancelar o boleto de uma fatura já paga.")
        return redirect('faturamento:list')
        
    with transaction.atomic():
        invoice.boleto_url = None
        invoice.save()
        
        # Atualiza também o Contas a Receber se existir
        from financeiro.models import AccountReceivable
        receivable = AccountReceivable.objects.filter(invoice=invoice).first()
        if receivable:
            receivable.cora_id = None
            receivable.cora_pdf_url = None
            receivable.cora_status = None
            receivable.save()
            
    messages.success(request, f"Boleto da fatura {invoice.number} cancelado com sucesso. Você pode gerar um novo agora.")
    return redirect('faturamento:list')

@login_required
@require_POST
def invoice_bulk_send_emails(request):
    """Envia e-mails em lote para faturas selecionadas."""
    import json
    
    invoice_ids = request.POST.getlist('invoice_ids[]')
    template_id = request.POST.get('template_id')
    
    if not invoice_ids:
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            template_id = data.get('template_id')
        except:
            pass
    
    if not invoice_ids:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma fatura selecionada.'}, status=400)
    
    invoices = Invoice.objects.filter(id__in=invoice_ids)
    success_count = 0
    errors = []
    
    try:
        from django.conf import settings
        use_brevo = bool(getattr(settings, 'BREVO_API_KEY', None))
        connection = None
        
        if not use_brevo:
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
        
        try:
            for invoice in invoices:
                try:
                    if not invoice.pdf_fatura:
                        print(f"[DEBUG] Gerando PDF faltante para fatura {invoice.number}")
                        pdf_bytes, pdf_err = generate_invoice_pdf_file(invoice)
                        invoice.refresh_from_db()

                    success, msg = BillingEmailService.send_invoice_email(invoice, template_id=template_id, connection=connection)
                    if success:
                        invoice.email_sent_at = timezone.now()
                        invoice.save()
                        success_count += 1
                    else:
                        invoice.email_status = 'ERRO'
                        invoice.save(update_fields=['email_status'])
                        errors.append(f"Fatura #{invoice.number}: {msg}")
                except Exception as e:
                    invoice.email_status = 'ERRO'
                    invoice.save(update_fields=['email_status'])
                    errors.append(f"Fatura #{invoice.number}: {str(e)}")
        finally:
            if connection:
                connection.close()
        
        return JsonResponse({
            'status': 'success' if success_count > 0 else 'error',
            'message': f'{success_count} e-mails enviados com sucesso.',
            'errors': errors
        })
    except Exception as e:
        error_msg = str(e)
        if "101" in error_msg or "unreachable" in error_msg.lower():
            advice = "Dica: O servidor não conseguiu alcançar o servidor de e-mail. Verifique se o EMAIL_HOST e EMAIL_PORT estão corretos no Railway."
        elif "authentication" in error_msg.lower() or "535" in error_msg:
            advice = "Dica: Usuário ou senha do e-mail incorretos. Verifique se a 'Senha de App' está correta."
        else:
            advice = ""
            
        return JsonResponse({
            'status': 'error',
            'message': f'Erro de Conexão: {error_msg}. {advice}'
        }, status=500)


@login_required
@require_POST
def invoice_bulk_generate_nfse(request):
    """Gera NFS-e em lote para faturas selecionadas (estrutura preparada)."""
    import json
    
    invoice_ids = request.POST.getlist('invoice_ids[]')
    if not invoice_ids:
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
        except:
            pass
    
    if not invoice_ids:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma fatura selecionada.'}, status=400)
    
    invoices = Invoice.objects.filter(id__in=invoice_ids, nfse_link__isnull=True)
    success_count = 0
    errors = []
    
    # TODO: Integrar com módulo nfse_nacional quando certificado configurado
    for invoice in invoices:
        try:
            # Placeholder - implementação real depende de certificado digital
            # from nfse_nacional.services.api_client import NFSeNacionalClient
            # client = NFSeNacionalClient()
            # result = client.emitir_nfse(invoice)
            # invoice.nfse_link = result.get('link')
            # invoice.save()
            # success_count += 1
            
            errors.append(f"Fatura #{invoice.id}: Emissão de NFS-e em desenvolvimento.")
        except Exception as e:
            errors.append(f"Fatura #{invoice.id}: {str(e)}")
    
    return JsonResponse({
        'status': 'info',
        'message': f'Funcionalidade de NFS-e em desenvolvimento. {success_count} notas processadas.',
        'errors': errors
    })


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
