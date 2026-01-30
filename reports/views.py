from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from financeiro.models import AccountReceivable, AccountPayable
from comercial.models import Contract
from operacional.models import ServiceOrder
import json

@login_required
def dashboard(request):
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # KPIs
    monthly_revenue = AccountReceivable.objects.filter(
        due_date__month=current_month, 
        due_date__year=current_year,
        status='RECEIVED' # Or PENDING + RECEIVED? Usually Revenue is what is billed or received. Let's use billed (all) or just received? Prompt says "Faturamento do Mês Atual (Soma de AccountReceivable do mês)". Usually means billed.
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    monthly_expenses = AccountPayable.objects.filter(
        due_date__month=current_month,
        due_date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    active_contracts = Contract.objects.filter(status='Ativo').count()
    
    open_os = ServiceOrder.objects.exclude(status='COMPLETED').exclude(status='CANCELED').count()

    # Chart Data (Last 6 months)
    labels = []
    revenue_data = []
    expense_data = []

    for i in range(5, -1, -1):
        date = today - timezone.timedelta(days=i*30) # Approx
        month = date.month
        year = date.year
        labels.append(f"{month}/{year}")
        
        rev = AccountReceivable.objects.filter(due_date__month=month, due_date__year=year).aggregate(Sum('amount'))['amount__sum'] or 0
        exp = AccountPayable.objects.filter(due_date__month=month, due_date__year=year).aggregate(Sum('amount'))['amount__sum'] or 0
        
        revenue_data.append(float(rev))
        expense_data.append(float(exp))

    context = {
        'monthly_revenue': monthly_revenue,
        'monthly_expenses': monthly_expenses,
        'active_contracts': active_contracts,
        'open_os': open_os,
        'chart_labels': json.dumps(labels),
        'revenue_data': json.dumps(revenue_data),
        'expense_data': json.dumps(expense_data),
    }

    return render(request, 'reports/dashboard.html', context)
