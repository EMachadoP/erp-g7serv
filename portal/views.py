from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from faturamento.models import Invoice
from operacional.models import ServiceOrder
from .models import ClientProfile

@login_required
def portal_home(request):
    try:
        profile = request.user.client_profile
        person = profile.person
        
        recent_invoices = Invoice.objects.filter(billing_group__contract__client=person).order_by('-issue_date')[:5]
        recent_os = ServiceOrder.objects.filter(client=person).order_by('-start_date')[:5]
        
        context = {
            'person': person,
            'recent_invoices': recent_invoices,
            'recent_os': recent_os,
        }
        return render(request, 'portal/home.html', context)
    except ClientProfile.DoesNotExist:
        return render(request, 'portal/no_profile.html')

@login_required
def portal_invoice_list(request):
    try:
        profile = request.user.client_profile
        person = profile.person
        invoices = Invoice.objects.filter(billing_group__contract__client=person).order_by('-issue_date')
        return render(request, 'portal/invoice_list.html', {'invoices': invoices})
    except ClientProfile.DoesNotExist:
        return render(request, 'portal/no_profile.html')

@login_required
def portal_os_list(request):
    try:
        profile = request.user.client_profile
        person = profile.person
        service_orders = ServiceOrder.objects.filter(client=person).order_by('-start_date')
        return render(request, 'portal/os_list.html', {'service_orders': service_orders})
    except ClientProfile.DoesNotExist:
        return render(request, 'portal/no_profile.html')
