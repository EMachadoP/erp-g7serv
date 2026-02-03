from django.shortcuts import render, get_object_or_404, redirect
from .models import AccountPayable, AccountReceivable, FinancialCategory, CashAccount, CostCenter, Receipt, BudgetPlan, BudgetItem, FinancialTransaction
from .forms import AccountPayableForm, AccountReceivableForm, ReceiptForm, PaymentPayableForm
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .integrations.cora import CoraService
from django.views.decorators.http import require_POST
import json
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
    
    if status:
        receivables = receivables.filter(status=status)
    if start_date:
        receivables = receivables.filter(due_date__gte=start_date)
    if end_date:
        receivables = receivables.filter(due_date__lte=end_date)
        
    return render(request, 'financeiro/account_receivable_list.html', {'receivables': receivables})

@login_required(login_url='/accounts/login/')
def account_receivable_update(request, pk):
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    if request.method == 'POST':
        form = AccountReceivableForm(request.POST, instance=receivable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta a receber atualizada com sucesso.')
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
        token = service.obter_token()
        
        if token:
            return HttpResponse(f"""
                <div style='color: green; font-family: sans-serif; padding: 20px;'>
                    <h1>✅ Conexão com Cora Stage: SUCESSO!</h1>
                    <p>O mTLS funcionou e o servidor obteve um Token válido.</p>
                    <p><b>Token parcial:</b> {token[:15]}...</p>
                </div>
            """)
        else:
            return HttpResponse(f"""
                <div style='color: red; font-family: sans-serif; padding: 20px;'>
                    <h1>❌ Falha na Conexão</h1>
                    <p>O certificado foi enviado, mas a Cora recusou. Verifique o Client-ID e os arquivos Base64.</p>
                </div>
            """, status=401)
            
    except Exception as e:
        return HttpResponse(f"Erro técnico: {str(e)}", status=500)

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
