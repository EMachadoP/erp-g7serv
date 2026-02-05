from django.shortcuts import render, get_object_or_404, redirect
from .models import AccountPayable, AccountReceivable, FinancialCategory, CashAccount, CostCenter, Receipt, BudgetPlan, BudgetItem, FinancialTransaction
from .forms import AccountPayableForm, AccountReceivableForm, ReceiptForm, PaymentPayableForm
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .integrations.cora import CoraService
from django.views.decorators.http import require_POST
import json
import requests
from core.models import Person
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.db import models, transaction
from decimal import Decimal

@login_required(login_url='/accounts/login/')
def account_payable_list(request):
    payables = AccountPayable.objects.all().order_by('due_date')
    
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status:
        payables = payables.filter(status=status)
    if start_date:
        payables = payables.filter(due_date__gte=start_date)
    if end_date:
        payables = payables.filter(due_date__lte=end_date)
        
    
    if status == 'PENDING':
        # Default sort by due date for pending
        payables = payables.order_by('due_date')
    else:
        payables = payables.order_by('-due_date')
        
    suppliers = Person.objects.filter(is_supplier=True).order_by('name')
    payment_form = PaymentPayableForm()
    
    return render(request, 'financeiro/account_payable_list.html', {
        'payables': payables,
        'contas': payables, # Alias for user template
        'contas_bancarias': CashAccount.objects.all(), # For manual modal
        'suppliers': suppliers,
        'payment_form': payment_form,
        'status_filter': status,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required(login_url='/accounts/login/')
def account_payable_create(request):
    if request.method == 'POST':
        form = AccountPayableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta a pagar criada com sucesso.')
            return redirect('financeiro:account_payable_list')
    else:
        form = AccountPayableForm()
    
    return render(request, 'financeiro/account_payable_form.html', {'form': form})

@login_required(login_url='/accounts/login/')
def account_payable_detail(request, pk):
    payable = get_object_or_404(AccountPayable, pk=pk)
    payment_form = PaymentPayableForm()
    return render(request, 'financeiro/account_payable_detail.html', {
        'payable': payable, 
        'payment_form': payment_form
    })

@login_required(login_url='/accounts/login/')
def baixa_conta_pagar(request, pk):
    payable = get_object_or_404(AccountPayable, pk=pk)
    
    if request.method == 'POST':
        form = PaymentPayableForm(request.POST)
        if form.is_valid():
            total_paid = form.cleaned_data['amount'] # This is the Total from form
            payment_date = form.cleaned_data['payment_date']
            account = form.cleaned_data['account']
            interest = form.cleaned_data['interest'] or 0
            fine = form.cleaned_data['fine'] or 0
            discount = form.cleaned_data['discount'] or 0
            notes = form.cleaned_data['notes']
            
            with transaction.atomic():
                # 1. Create Transaction (OUT)
                # Ensure category exists or use the payable's category
                FinancialTransaction.objects.create(
                    description=f"Pagamento {payable.description}",
                    amount=total_paid,
                    transaction_type='OUT',
                    date=payment_date,
                    account=account,
                    category=payable.category,
                    related_payable=payable
                )
                
                # 2. Update Payable
                # Force explicit status update
                payable.status = 'PAID'
                payable.payment_date = payment_date
                payable.amount = total_paid  # "valor_pago" logic
                payable.account = account
                
                # Store breakdown in notes
                breakdown = f"Pago: R$ {total_paid} (Original: {payable.amount} + Juros: {interest} + Multa: {fine} - Desc: {discount})"
                if notes:
                    payable.notes = f"{payable.notes or ''} | {breakdown} | Obs: {notes}"
                else:
                     payable.notes = f"{payable.notes or ''} | {breakdown}"

                payable.save()
                
                messages.success(request, f'Pagamento registrado! Valor Total: R$ {total_paid}. Saldo da conta {account.name} atualizado.')
            
            return redirect('financeiro:account_payable_detail', pk=pk)
    
    return redirect('financeiro:account_payable_list')

@login_required(login_url='/accounts/login/')
def realizar_baixa_conta(request, pk):
    payable = get_object_or_404(AccountPayable, pk=pk)
    
    if request.method == 'POST':
        try:
            # Get data from manual form
            account_id = request.POST.get('conta_saida')
            payment_date = request.POST.get('data_pagamento')
            
            # Helper to parse decimal from string or default to 0
            def parse_decimal(val):
                if not val: return Decimal('0.00')
                return Decimal(str(val).replace(',', '.'))

            interest = parse_decimal(request.POST.get('juros'))
            fine = parse_decimal(request.POST.get('multa'))
            discount = parse_decimal(request.POST.get('desconto'))
            
            # Calculate total (Verification)
            # Ensure payable.amount is Decimal
            original = payable.amount 
            total_paid = original + interest + fine - discount
            
            account = get_object_or_404(CashAccount, pk=account_id)
            
            with transaction.atomic():
                # 1. Create Transaction (OUT)
                FinancialTransaction.objects.create(
                    description=f"Pagamento {payable.description}",
                    amount=total_paid,
                    transaction_type='OUT',
                    date=payment_date,
                    account=account,
                    category=payable.category,
                    related_payable=payable
                )
                
                # 2. Update Payable
                payable.status = 'PAID'
                payable.payment_date = payment_date
                payable.amount = total_paid
                payable.account = account
                
                breakdown = f"Pago: R$ {total_paid:.2f} (Orig: {original:.2f} + J: {interest:.2f} + M: {fine:.2f} - D: {discount:.2f})"
                if payable.notes:
                    payable.notes += f" | {breakdown}"
                else:
                    payable.notes = breakdown
                    
                payable.save()
                
                # Update Account Balance handled by FinancialTransaction.save() signal/override
                # account.current_balance -= total_paid 
                # account.save()
                
                messages.success(request, f'Pagamento de R$ {total_paid:.2f} realizado com sucesso!')
                
        except Exception as e:
            print(f"DEBUG ERROR: {e}") 
            messages.error(request, f'Erro ao realizar baixa: {str(e)}')
            
    return redirect('financeiro:account_payable_list')


@login_required(login_url='/accounts/login/')
def estornar_conta_pagar(request, pk):
    payable = get_object_or_404(AccountPayable, pk=pk)
    
    if request.method == 'POST':
        if payable.status != 'PAID':
             messages.error(request, 'Apenas contas pagas podem ser estornadas.')
             return redirect('financeiro:account_payable_list')

        try:
            with transaction.atomic():
                txs = FinancialTransaction.objects.filter(related_payable=payable)
                for tx in txs:
                    tx.delete() 
                
                payable.status = 'PENDING'
                payable.payment_date = None
                payable.account = None
                
                import re
                match = re.search(r'Orig: ([\d\.,]+)', payable.notes or '')
                if match:
                    try:
                        payable.amount = Decimal(match.group(1).replace(',', '.'))
                    except:
                        pass
                
                payable.save()
                messages.success(request, 'Pagamento estornado com sucesso!')
                
        except Exception as e:
            messages.error(request, f'Erro ao estornar: {str(e)}')
            
    return redirect('financeiro:account_payable_list')


@login_required(login_url='/accounts/login/')
def cancelar_conta_pagar(request, pk):
    payable = get_object_or_404(AccountPayable, pk=pk)
    if request.method == 'POST':
        # If it was paid, we technically should reverse current accounting (add money back?)
        # For now, just setting status is what's requested. 
        # "estorna se já pago" -> Reverses logic implies we acknowledged we didn't pay.
        payable.status = 'CANCELLED'
        # Clear payment info to avoid confusion
        payable.payment_date = None
        payable.account = None
        payable.save()
        messages.success(request, 'Conta cancelada com sucesso.')
        return redirect('financeiro:account_payable_list')
    return redirect('financeiro:account_payable_list')

@login_required(login_url='/accounts/login/')
def account_receivable_list(request):
    receivables = AccountReceivable.objects.all().order_by('due_date')
    
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('q', '')
    
    if search_query:
        receivables = receivables.filter(
            Q(description__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(document_number__icontains=search_query) |
            Q(external_reference__icontains=search_query)
        )
        
    if status:
        receivables = receivables.filter(status=status)
    if start_date:
        receivables = receivables.filter(due_date__gte=start_date)
    if end_date:
        receivables = receivables.filter(due_date__lte=end_date)
        
    # Default sort by due date for pending, else descending due date
    if status == 'PENDING':
        receivables = receivables.order_by('due_date')
    else:
        receivables = receivables.order_by('-due_date')

    # Get email templates for bulk actions
    from core.models import EmailTemplate
    email_templates = EmailTemplate.objects.filter(active=True)
    
    return render(request, 'financeiro/account_receivable_list.html', {
        'receivables': receivables,
        'status_filter': status,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
        'email_templates': email_templates
    })

@login_required
def sync_receables_view(request):
    """View manual para garantir que todas as faturas tenham um contas a receber."""
    if not request.user.is_superuser:
        messages.error(request, "Acesso negado.")
        return redirect('financeiro:account_receivable_list')
        
    from faturamento.models import Invoice
    from .models import AccountReceivable, FinancialCategory
    
    # Busca todas as faturas, forçando active=True para garantir visibilidade
    invoices = Invoice.objects.all()
    created_count = 0
    skipped_count = 0
    
    # Categoria padrão usada no Faturamento de Contratos
    category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Contratos",
        defaults={'type': 'REVENUE'}
    )
    
    from integracao_cora.models import BoletoCora
    
    # Ajuste temporário para o ELDON se solicitado
    eldon_inv = Invoice.objects.filter(client__name__icontains='ELDON', amount=5.00).first()
    if eldon_inv:
        eldon_inv.status = 'PG'
        eldon_inv.save()

    # Categorias
    fatura_category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Faturas",
        defaults={'type': 'REVENUE'}
    )
    contrato_category, _ = FinancialCategory.objects.get_or_create(
        name="Receita de Contratos",
        defaults={'type': 'REVENUE'}
    )
    
    for inv in invoices:
        receivable = AccountReceivable.objects.filter(invoice=inv).first()
        
        # Determine correct status
        target_status = 'PENDING'
        # Check internal status OR Cora payment
        cora_paid = BoletoCora.objects.filter(fatura=inv, status='Pago').exists()
        if inv.status == 'PG' or cora_paid:
            target_status = 'RECEIVED'
            if cora_paid and inv.status != 'PG':
                inv.status = 'PG'
                inv.save()
        elif inv.status == 'CN':
            target_status = 'CANCELLED'

        # Determine correct category
        target_category = contrato_category if inv.contract else fatura_category

        if not receivable:
            description = f"Fatura #{inv.number}"
            if inv.client:
                description += f" - {inv.client.name}"
            
            AccountReceivable.objects.create(
                description=description,
                client=inv.client,
                category=target_category,
                amount=inv.amount,
                due_date=inv.due_date,
                status=target_status,
                invoice=inv,
                document_number=inv.number,
                active=True,
                receipt_date=timezone.now().date() if target_status == 'RECEIVED' else None
            )
            created_count += 1
        else:
            # Sync status and category if different
            changed = False
            if receivable.status != target_status:
                receivable.status = target_status
                if target_status == 'RECEIVED' and not receivable.receipt_date:
                    receivable.receipt_date = timezone.now().date()
                changed = True
            
            if receivable.category != target_category:
                receivable.category = target_category
                changed = True
                
            if changed:
                receivable.save()
            skipped_count += 1
            
    messages.success(request, f"Sincronização concluída! Criados: {created_count}, Atualizados/Existentes: {skipped_count}.")
    return redirect('financeiro:account_receivable_list')

@login_required
def receivables_diagnostics(request):
    """View de diagnóstico com busca de itens cancelados para recuperação."""
    if not request.user.is_superuser:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Acesso negado'}, status=403)
        
    from faturamento.models import Invoice
    from .models import AccountReceivable
    from comercial.models import Budget, Contract
    from operacional.models import ServiceOrder
    from django.http import JsonResponse
    
    # Busca itens cancelados recentemente para ajudar o usuário
    data = {
        'recent_invoices': [],
        'cancelled_budgets': [],
        'cancelled_sos': [],
        'cancelled_invoices': []
    }
    
    # Invoices recentes
    invoices = Invoice.objects.all().order_by('-updated_at')[:50]
    for inv in invoices:
        receivable = AccountReceivable.objects.filter(invoice=inv).first()
        data['recent_invoices'].append({
            'id': inv.id,
            'number': inv.number,
            'client': inv.client.name if inv.client else "N/A",
            'status': inv.status,
            'has_receivable': receivable is not None,
            'receivable_status': receivable.status if receivable else None,
            'updated_at': inv.updated_at.isoformat()
        })
        if inv.status == 'CN':
            data['cancelled_invoices'].append(data['recent_invoices'][-1])

    # Orçamentos cancelados
    budgets = Budget.objects.filter(status='Cancelado').order_by('-updated_at')[:10]
    for b in budgets:
        data['cancelled_budgets'].append({
            'id': b.id,
            'title': b.title,
            'client': b.client.name,
            'updated_at': b.updated_at.isoformat()
        })

    # OS canceladas
    sos = ServiceOrder.objects.filter(status='CANCELED').order_by('-updated_at')[:10]
    for s in sos:
        data['cancelled_sos'].append({
            'id': s.id,
            'client': s.client.name,
            'updated_at': s.updated_at.isoformat()
        })

    return JsonResponse(data)

@login_required(login_url='/accounts/login/')
def account_receivable_update(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    if request.method == 'POST':
        form = AccountReceivableForm(request.POST, instance=receivable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta a receber atualizada com sucesso.')
            # If we came from detail, return to detail
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('financeiro:account_receivable_list')
    else:
        form = AccountReceivableForm(instance=receivable)
    
    return render(request, 'financeiro/account_receivable_form.html', {
        'form': form,
        'receivable': receivable
    })

@staff_member_required
def testar_conexao_cora(request):
    try:
        service = CoraService()
        # Vamos capturar a resposta bruta aqui
        payload = {
            "grant_type": "client_credentials",
            "client_id": service.client_id
        }
        
        response = requests.post(
            service.auth_url, 
            data=payload, 
            cert=service.cert_pair, 
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        
        status = response.status_code
        texto_erro = response.text

        if status == 200:
            token = response.json().get('access_token', 'N/A')
            return HttpResponse(f"<h1 style='color:green; font-family: sans-serif;'>✅ Sucesso! Token: {token[:10]}...</h1>")
        else:
            return HttpResponse(f"""
                <div style="font-family: sans-serif; padding: 20px;">
                    <h1 style='color:red'>❌ Erro {status}</h1>
                    <p><b>Resposta da Cora:</b> {texto_erro}</p>
                    <hr>
                    <p><b>Dica Técnica:</b> Se for 401, o Client-ID ou Certificado estão errados. Se for 403, o certificado não tem permissão de 'Partner'.</p>
                </div>
            """, status=status)
            
    except Exception as e:
        return HttpResponse(f"<h1 style='color:orange; font-family: sans-serif;'>⚠️ Erro de Infra: {str(e)}</h1>", status=500)

@login_required(login_url='/accounts/login/')
def account_receivable_create(request):
    if request.method == 'POST':
        form = AccountReceivableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta a receber criada com sucesso.')
            return redirect('financeiro:account_receivable_list')
    else:
        form = AccountReceivableForm()
    
    return render(request, 'financeiro/account_receivable_form.html', {'form': form})

@login_required(login_url='/accounts/login/')
def account_receivable_detail(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    return render(request, 'financeiro/account_receivable_detail.html', {'receivable': receivable})

@login_required(login_url='/accounts/login/')
def account_receivable_receive(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    if request.method == 'POST':
        receivable.status = 'RECEIVED'
        receivable.receipt_date = timezone.now().date()
        receivable.save()
        messages.success(request, 'Recebimento registrado com sucesso.')
        return redirect('financeiro:account_receivable_detail', pk=pk)
    return redirect('financeiro:account_receivable_detail', pk=pk)

@login_required(login_url='/accounts/login/')
def emitir_boleto_cora(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    
    if not receivable.client:
        messages.error(request, "Cliente não vinculado a esta conta.")
        return redirect('financeiro:account_receivable_detail', pk=pk)
    
    # 1. Prepare Cora Payload
    service = CoraService()
    
    # Amount in cents
    amount_cents = int(receivable.amount * 100)
    client = receivable.client
    
    # Customer Address
    address_data = {
        "street": client.address or "Não informado",
        "number": client.number or "S/N",
        "district": client.neighborhood or "Centro",
        "city": client.city or "Recife",
        "state": client.state or "PE",
        "zip_code": client.zip_code.replace('-', '').replace(' ', '') if client.zip_code else "00000000"
    }
    
    # Cora payload structure (Invoice v2)
    fatura_data = {
        "customer": {
            "name": client.name,
            "email": client.email or "financeiro@descartex.com.br",
            "document": {
                "identity": client.document.replace('.', '').replace('-', '').replace('/', '').replace(' ', ''),
                "type": "CNPJ" if len(client.document.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')) > 11 else "CPF"
            },
            "address": address_data
        },
        "services": [
            {
                "name": f"{receivable.description} ({receivable.external_reference or ''})",
                "amount": amount_cents
            }
        ],
        "payment_options": ["BANK_SLIP", "PIX"],
        "due_date": receivable.due_date.isoformat()
    }
    
    # Add configurations for Fine (Multa) and Interest (Juros) if set
    configs = {}
    if receivable.fine_amount > 0:
        # Cora fine is usually in cents
        configs["fine"] = {"amount": int(receivable.fine_amount * 100)}
    
    if receivable.interest_percent > 0:
        # Cora interest is rate per month
        configs["interest"] = {"rate": float(receivable.interest_percent)}
        
    if configs:
        fatura_data["configurations"] = configs
    
    # 2. Call Cora
    result = service.gerar_fatura(fatura_data)
    
    if "erro" in result:
        messages.error(request, f"Erro ao emitir na Cora: {result['erro']}")
    elif "id" in result:
        # Success! Save data
        receivable.cora_id = result.get('id')
        receivable.cora_status = result.get('status')
        
        # Get link/copy-paste
        p_options = result.get('payment_options', [])
        for opt in p_options:
            if opt.get('type') == 'BANK_SLIP':
                receivable.cora_copy_paste = opt.get('copy_paste')
                receivable.cora_pdf_url = opt.get('bank_slip_url')
        
        receivable.save()
        messages.success(request, f"Boleto Cora emitido com sucesso! ID: {receivable.cora_id}")
    else:
        messages.warning(request, f"Resposta inesperada da Cora: {json.dumps(result)}")

    return redirect('financeiro:account_receivable_detail', pk=pk)

@login_required(login_url='/accounts/login/')
def account_receivable_cancel(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    if request.method == 'POST':
        receivable.status = 'CANCELLED'
        receivable.save()
        messages.success(request, 'Conta cancelada com sucesso.')
        return redirect('financeiro:account_receivable_list')
    return redirect('financeiro:account_receivable_detail', pk=pk)

@login_required(login_url='/accounts/login/')
def financial_dashboard(request):
    total_payables = sum(p.amount for p in AccountPayable.objects.filter(status='PENDING'))
    total_receivables = sum(r.amount for r in AccountReceivable.objects.filter(status='PENDING'))
    balance = total_receivables - total_payables
    
    recent_payables = AccountPayable.objects.order_by('due_date')[:5]
    recent_receivables = AccountReceivable.objects.order_by('due_date')[:5]
    
    context = {
        'total_payables': total_payables,
        'total_receivables': total_receivables,
        'balance': balance,
        'recent_payables': recent_payables,
        'recent_receivables': recent_receivables,
    }
    return render(request, 'financeiro/dashboard.html', context)

@login_required(login_url='/accounts/login/')
def receipt_list(request):
    receipts = Receipt.objects.all().order_by('-issue_date')
    
    search_query = request.GET.get('search')
    if search_query:
        receipts = receipts.filter(
            Q(description__icontains=search_query) | 
            Q(person__name__icontains=search_query) |
            Q(person__fantasy_name__icontains=search_query)
        )
        
    return render(request, 'financeiro/receipt_list.html', {'receipts': receipts})

@login_required(login_url='/accounts/login/')
def receipt_create(request):
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recibo gerado com sucesso.')
            return redirect('financeiro:receipt_list')
    else:
        form = ReceiptForm()
    
    return render(request, 'financeiro/receipt_form.html', {'form': form})

@login_required(login_url='/accounts/login/')
def receipt_print(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    return render(request, 'financeiro/receipt_print.html', {'receipt': receipt})

@login_required(login_url='/accounts/login/')
def budget_plan_list(request):
    plans = BudgetPlan.objects.all().order_by('-year')
    return render(request, 'financeiro/budget_plan_list.html', {'plans': plans})

@login_required(login_url='/accounts/login/')
def budget_plan_create(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        description = request.POST.get('description')
        if year:
            try:
                plan = BudgetPlan.objects.create(year=year, description=description)
                messages.success(request, f'Planejamento para {year} criado com sucesso.')
                return redirect('financeiro:budget_plan_detail', pk=plan.pk)
            except Exception as e:
                messages.error(request, f'Erro ao criar planejamento: {e}')
    return redirect('financeiro:budget_plan_list')

@login_required(login_url='/accounts/login/')
def budget_plan_detail(request, pk):
    plan = get_object_or_404(BudgetPlan, pk=pk)
    categories = FinancialCategory.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    
    # Structure: {category_id: {month: {planned: 0, realized: 0}}}
    data = {}
    
    # Initialize with planned values
    items = BudgetItem.objects.filter(plan=plan)
    for item in items:
        if item.category_id not in data:
            data[item.category_id] = {}
        if item.month not in data[item.category_id]:
            data[item.category_id][item.month] = {'planned': 0, 'realized': 0}
        data[item.category_id][item.month]['planned'] = item.amount

    # Calculate realized values (Expenses)
    expenses = AccountPayable.objects.filter(
        due_date__year=plan.year,
        status='PAID'
    ).values('category', 'due_date__month').annotate(total=models.Sum('amount'))
    
    for exp in expenses:
        cat_id = exp['category']
        month = exp['due_date__month']
        if cat_id:
            if cat_id not in data:
                data[cat_id] = {}
            if month not in data[cat_id]:
                data[cat_id][month] = {'planned': 0, 'realized': 0}
            data[cat_id][month]['realized'] += exp['total']

    # Calculate realized values (Revenues)
    revenues = AccountReceivable.objects.filter(
        due_date__year=plan.year,
        status='RECEIVED'
    ).values('category', 'due_date__month').annotate(total=models.Sum('amount'))
    
    for rev in revenues:
        cat_id = rev['category']
        month = rev['due_date__month']
        if cat_id:
            if cat_id not in data:
                data[cat_id] = {}
            if month not in data[cat_id]:
                data[cat_id][month] = {'planned': 0, 'realized': 0}
            data[cat_id][month]['realized'] += rev['total']

    # Pass data to template in a way that's easy to iterate
    # We'll attach 'budget_data' to category objects for the template
    def attach_data(category):
        category.budget_data = {}
        for month in range(1, 13):
            category.budget_data[month] = data.get(category.id, {}).get(month, {'planned': 0, 'realized': 0})
        
        for sub in category.subcategories.all():
            attach_data(sub)
            
    for cat in categories:
        attach_data(cat)

    months = range(1, 13)
    return render(request, 'financeiro/budget_plan_detail.html', {
        'plan': plan,
        'categories': categories,
        'months': months
    })

@login_required
@require_POST
def budget_item_update(request):
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        category_id = data.get('category_id')
        month = data.get('month')
        amount = data.get('amount')
        
        plan = BudgetPlan.objects.get(pk=plan_id)
        category = FinancialCategory.objects.get(pk=category_id)
        
        item, created = BudgetItem.objects.update_or_create(
            plan=plan,
            category=category,
            month=month,
            defaults={'amount': amount}
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
@login_required
@require_POST
def bulk_generate_boletos(request):
    """
    Gera boletos em lote para os IDs selecionados.
    """
    receivable_ids = request.POST.getlist('receivable_ids[]')
    if not receivable_ids:
        # Tenta pegar via corpo JSON se for chamado via Fetch/JS direto
        try:
            data = json.loads(request.body)
            receivable_ids = data.get('receivable_ids', [])
        except:
            pass

    if not receivable_ids:
        return JsonResponse({'status': 'error', 'message': 'Nenhum item selecionado.'}, status=400)

    receivables = AccountReceivable.objects.filter(id__in=receivable_ids, cora_id__isnull=True)
    cora = CoraService()
    success_count = 0
    errors = []

    for receivable in receivables:
        try:
            # Payload format according to Cora v2
            fatura_data = {
                "customer": {
                    "name": receivable.client.name,
                    "email": receivable.client.email or "faturamento@g7serv.com.br",
                    "document": {
                        "identity": receivable.client.document or "00000000000",
                        "type": "CNPJ" if len(receivable.client.document or "") > 11 else "CPF"
                    }
                },
                "payment_methods": ["BANK_SLIP", "PIX"],
                "services": [
                    {
                        "name": receivable.description,
                        "amount": int(receivable.amount * 100),
                        "quantity": 1
                    }
                ],
                "due_date": receivable.due_date.strftime("%Y-%m-%d")
            }
            
            cora_response = cora.gerar_fatura(fatura_data)
            
            if "payment_url" in cora_response or "id" in cora_response:
                receivable.cora_id = cora_response.get("id")
                receivable.cora_pdf_url = cora_response.get("url") or cora_response.get("payment_url")
                receivable.cora_status = cora_response.get("status", "OPEN")
                receivable.save()
                success_count += 1
            else:
                errors.append(f"Recebível #{receivable.id}: {cora_response.get('erro', 'Erro desconhecido')}")
        except Exception as e:
            errors.append(f"Recebível #{receivable.id}: {str(e)}")

    return JsonResponse({
        'status': 'success', 
        'message': f'{success_count} boletos gerados com sucesso.',
        'errors': errors
    })

@login_required
@require_POST
def bulk_send_emails(request):
    """
    Envia e-mails em lote para os IDs selecionados.
    """
    receivable_ids = request.POST.getlist('receivable_ids[]')
    template_id = request.POST.get('template_id')
    
    if not receivable_ids:
        try:
            data = json.loads(request.body)
            receivable_ids = data.get('receivable_ids', [])
            template_id = data.get('template_id')
        except:
            pass

    if not receivable_ids:
        return JsonResponse({'status': 'error', 'message': 'Nenhum item selecionado.'}, status=400)

    receivables = AccountReceivable.objects.filter(id__in=receivable_ids)
    success_count = 0
    errors = []

    from django.core.mail import get_connection
    connection = get_connection()
    connection.open()
    
    try:
        for receivable in receivables:
            if not receivable.invoice:
                errors.append(f"Recebível #{receivable.id}: Não possui fatura vinculada.")
                continue

            try:
                if BillingEmailService.send_invoice_email(receivable.invoice, template_id=template_id, connection=connection):
                    receivable.invoice.email_sent_at = timezone.now()
                    receivable.invoice.save()
                    success_count += 1
                else:
                    errors.append(f"Recebível #{receivable.id}: Falha ao enviar e-mail.")
            except Exception as e:
                errors.append(f"Recebível #{receivable.id}: {str(e)}")
    finally:
        connection.close()

    return JsonResponse({
        'status': 'success', 
        'message': f'{success_count} e-mails enviados com sucesso.',
        'errors': errors
    })
