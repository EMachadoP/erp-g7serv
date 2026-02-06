from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError
from django.views import View
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.utils import timezone
from django.contrib import messages
import base64
from .models import Contract, Budget, BudgetProduct, BudgetService, ContractTemplate, BillingGroup, ContractItem
from .forms import BillingGroupForm, ContractForm, ContractItemFormSet
from core.models import Person, Service
from estoque.models import Product
from django.core.management import call_command
import io
import re

class ContractSigningView(View):
    def get(self, request, token):
        contract = get_object_or_404(Contract, token=token)
        
        if contract.status != 'Ativo':
             # You might want to show a different page if expired or cancelled
             pass

        # Variable substitution
        content = replace_contract_variables(contract.template.content, contract)

        return render(request, 'comercial/contract_signing.html', {
            'contract': contract,
            'content': content
        })

    def post(self, request, token):
        contract = get_object_or_404(Contract, token=token)
        
        signature_data = request.POST.get('signature_data') # Base64 image
        
        if signature_data:
            format, imgstr = signature_data.split(';base64,') 
            ext = format.split('/')[-1] 
            data = base64.b64decode(imgstr) 
            file_name = f"signature_{contract.id}.{ext}"
            
            contract.signature_image.save(file_name, ContentFile(data), save=False)
            contract.signed_at = timezone.now()
            contract.signed_ip = self.get_client_ip(request)
            contract.save()
            
            return render(request, 'comercial/contract_signed_success.html', {'contract': contract})
        
        return redirect('contract_signing', token=token)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def replace_contract_variables(content, contract):
    """
    Helper function to replace placeholders in contract content with actual data.
    """
    from django.utils.formats import date_format
    
    # Helper for case-insensitive replacement
    def replace_ignore_case(text, pattern, replacement):
        return re.sub(pattern, str(replacement), text, flags=re.IGNORECASE)

    # Client Data
    content = replace_ignore_case(content, r'{{cliente_nome}}', contract.client.name)
    content = replace_ignore_case(content, r'{{NOME_CLIENTE}}', contract.client.name)
    
    doc = contract.client.document or ''
    # Format CNPJ/CPF
    if len(doc) == 14: # CNPJ
        formatted_doc = f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
    elif len(doc) == 11: # CPF
        formatted_doc = f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
    else:
        formatted_doc = doc
        
    content = replace_ignore_case(content, r'{{CNPJ_CPF_CLIENTE}}', formatted_doc)
    
    resp_name = contract.client.responsible_name or ''
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    # logger.info(f"Replacing variables for contract {contract.id}. Resp Name: {resp_name}")
    
    # Robust replacement for responsible name (accents, spaces, underscores, HTML entities)
    # Matches {{NOME...S...NDICO...OU...RESPONS...VEL}} with any chars in between
    content = replace_ignore_case(content, r'{{NOME.*?S.*?NDICO.*?OU.*?RESPONS.*?VEL}}', resp_name)
    
    # Keep specific ones just in case
    content = replace_ignore_case(content, r'{{NOME[_\s]S[IÍ]NDICO[_\s]OU[_\s]RESPONS[AÁ]VEL}}', resp_name)
    content = content.replace('{{NOME_SÍNDICO_OU_RESPONSÁVEL}}', resp_name)
    content = replace_ignore_case(content, r'{{NOME_RESPONSAVEL}}', resp_name)
    
    resp_cpf = contract.client.responsible_cpf or ''
    content = replace_ignore_case(content, r'{{CPF}}', resp_cpf)
    content = replace_ignore_case(content, r'{{CPF_RESPONSAVEL}}', resp_cpf)
    
    # Address
    address_parts = []
    if contract.client.address: address_parts.append(contract.client.address)
    if contract.client.number: address_parts.append(contract.client.number)
    if contract.client.neighborhood: address_parts.append(contract.client.neighborhood)
    if contract.client.city: address_parts.append(contract.client.city)
    if contract.client.state: address_parts.append(contract.client.state)
    if contract.client.zip_code: address_parts.append(f"CEP: {contract.client.zip_code}")
    
    full_address = ", ".join(address_parts)
    content = replace_ignore_case(content, r'{{ENDERECO_CLIENTE}}', full_address)

    content = replace_ignore_case(content, r'{{EMAIL_CLIENTE}}', contract.client.email or '')
    content = replace_ignore_case(content, r'{{TELEFONE_CLIENTE}}', contract.client.phone or '')

    # Contract Data
    formatted_value = f"{contract.value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    content = replace_ignore_case(content, r'{{valor}}', formatted_value)
    content = replace_ignore_case(content, r'{{VALOR[_\s]MENSAL([_\s]DO[_\s]CONTRATO)?}}', formatted_value)
    
    content = replace_ignore_case(content, r'{{DIA_VENCIMENTO}}', str(contract.due_day))
    
    if contract.start_date:
        content = replace_ignore_case(content, r'{{DATA_INICIO}}', date_format(contract.start_date, "d/m/Y"))
        content = replace_ignore_case(content, r'{{DIA}}', str(contract.start_date.day))
        month_name = date_format(contract.start_date, "F") 
        content = replace_ignore_case(content, r'{{MÊS POR EXTENSO}}', month_name.lower())
        content = replace_ignore_case(content, r'{{ANO}}', str(contract.start_date.year))
    else:
        content = replace_ignore_case(content, r'{{DATA_INICIO}}', '')
        content = replace_ignore_case(content, r'{{DIA}}', '')
        content = replace_ignore_case(content, r'{{MÊS POR EXTENSO}}', '')
        content = replace_ignore_case(content, r'{{ANO}}', '')

    # Signature Date
    if contract.signed_at:
        content = replace_ignore_case(content, r'{{DATA_ASSINATURA}}', date_format(contract.signed_at, "d/m/Y"))
    else:
        # Placeholder for signature date
        content = replace_ignore_case(content, r'{{DATA_ASSINATURA}}', '__________________')

    return content

from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def client_list(request):
    search_query = request.GET.get('search', '')
    
    clients = Person.objects.filter(is_client=True).order_by('name')
    
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) | 
            Q(document__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comercial/client_list.html', {'page_obj': page_obj, 'search_query': search_query})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Person, pk=pk, is_client=True)
    return render(request, 'comercial/client_detail.html', {'client': client})

@login_required
def client_create(request):
    if request.method == 'POST':
        # Simple manual form handling for now, can be upgraded to Django Forms later
        try:
            Person.objects.create(
                is_client=request.POST.get('is_client') == 'on',
                is_supplier=request.POST.get('is_supplier') == 'on',
                is_final_consumer=request.POST.get('is_final_consumer') == 'on',
                name=request.POST.get('name'),
                fantasy_name=request.POST.get('fantasy_name'),
                person_type=request.POST.get('person_type', 'PJ') or 'PJ',
                document=request.POST.get('document'),
                state_registration=request.POST.get('state_registration'),
                responsible_name=request.POST.get('responsible_name'),
                responsible_cpf=request.POST.get('responsible_cpf'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                zip_code=request.POST.get('zip_code'),
                address=request.POST.get('address'),
                number=request.POST.get('number'),
                complement=request.POST.get('complement'),
                neighborhood=request.POST.get('neighborhood'),
                city=request.POST.get('city'),
                state=request.POST.get('state')
            )
            messages.success(request, 'Cliente cadastrado com sucesso.')
            return redirect('comercial:client_list')
        except IntegrityError:
            messages.error(request, 'Erro: Já existe um cliente cadastrado com este CPF/CNPJ.')
            return render(request, 'comercial/client_form_v2.html', {
                'client': None,
                'pj_checked': 'checked' if request.POST.get('person_type') == 'PJ' else '',
                'pf_checked': 'checked' if request.POST.get('person_type') == 'PF' else '',
                'is_client_checked': 'checked' if request.POST.get('is_client') == 'on' else '',
                'is_supplier_checked': 'checked' if request.POST.get('is_supplier') == 'on' else '',
                'is_final_consumer_checked': 'checked' if request.POST.get('is_final_consumer') == 'on' else '',
                'form_data': request.POST
            })
    
    return render(request, 'comercial/client_form_v2.html', {
        'client': None,
        'form_data': None,
        'pj_checked': 'checked',
        'pf_checked': '',
        'is_client_checked': 'checked', # Default for new client
        'is_supplier_checked': '',
        'is_final_consumer_checked': ''
    })

@login_required
def client_update(request, pk):
    client = get_object_or_404(Person, pk=pk, is_client=True)
    
    if request.method == 'POST':
        client.is_client = request.POST.get('is_client') == 'on'
        client.is_supplier = request.POST.get('is_supplier') == 'on'
        client.is_final_consumer = request.POST.get('is_final_consumer') == 'on'
        client.name = request.POST.get('name')
        client.fantasy_name = request.POST.get('fantasy_name')
        client.person_type = request.POST.get('person_type') or client.person_type or 'PJ'
        client.document = request.POST.get('document')
        client.state_registration = request.POST.get('state_registration')
        client.responsible_name = request.POST.get('responsible_name')
        client.responsible_cpf = request.POST.get('responsible_cpf')
        client.email = request.POST.get('email')
        client.phone = request.POST.get('phone')
        client.zip_code = request.POST.get('zip_code')
        client.address = request.POST.get('address')
        client.number = request.POST.get('number')
        client.complement = request.POST.get('complement')
        client.neighborhood = request.POST.get('neighborhood')
        client.city = request.POST.get('city')
        client.state = request.POST.get('state')
        try:
            client.save()
            messages.success(request, 'Cliente atualizado com sucesso.')
            return redirect('comercial:client_list')
        except IntegrityError:
            messages.error(request, 'Erro: Já existe um cliente cadastrado com este CPF/CNPJ.')
            # No need for manual state preservation here as we are editing an instance
            return render(request, 'comercial/client_form_v2.html', {
                'client': client,
                'form_data': request.POST,
                'pj_checked': 'checked' if request.POST.get('person_type') == 'PJ' else '',
                'pf_checked': 'checked' if request.POST.get('person_type') == 'PF' else '',
                'is_client_checked': 'checked' if request.POST.get('is_client') == 'on' else '',
                'is_supplier_checked': 'checked' if request.POST.get('is_supplier') == 'on' else '',
                'is_final_consumer_checked': 'checked' if request.POST.get('is_final_consumer') == 'on' else ''
            })
        
    pj_checked = 'checked' if client.person_type == 'PJ' else ''
    pf_checked = 'checked' if client.person_type == 'PF' else ''
    
    return render(request, 'comercial/client_form_v2.html', {
        'client': client,
        'form_data': None,
        'pj_checked': pj_checked,
        'pf_checked': pf_checked,
        'is_client_checked': 'checked' if client.is_client else '',
        'is_supplier_checked': 'checked' if client.is_supplier else '',
        'is_final_consumer_checked': 'checked' if client.is_final_consumer else ''
    })

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Person, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente excluído com sucesso.')
        return redirect('comercial:client_list')
        
    return render(request, 'comercial/client_confirm_delete.html', {'client': client})

@login_required
def contract_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    contracts = Contract.objects.all().order_by('-created_at')
    
    if search_query:
        contracts = contracts.filter(client__name__icontains=search_query)
        
    if status_filter:
        contracts = contracts.filter(status=status_filter)
        
    paginator = Paginator(contracts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comercial/contract_list.html', {
        'page_obj': page_obj, 
        'search_query': search_query,
        'status_filter': status_filter
    })

@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'comercial/contract_detail.html', {'contract': contract})

@login_required
def contract_create(request):
    if request.method == 'POST':
        form = ContractForm(request.POST)
        formset = ContractItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            contract = form.save(commit=False)
            contract.value = 0 # Will be updated after saving items
            contract.save()
            
            items = formset.save(commit=False)
            total_value = 0
            for item in items:
                item.contract = contract
                item.save()
                total_value += item.total_price
            
            contract.value = total_value
            contract.save(update_fields=['value'])
            
            messages.success(request, 'Contrato criado com sucesso.')
            return redirect('comercial:contract_detail', pk=contract.pk)
    else:
        form = ContractForm()
        formset = ContractItemFormSet()
        
    return render(request, 'comercial/contract_form_fixed.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    # Create initial item for legacy contracts if none exist
    if not contract.items.exists() and contract.value > 0:
        ContractItem.objects.create(
            contract=contract,
            category='MANUTENCAO',
            description=f"Serviço de Manutenção",
            quantity=1,
            unit_price=contract.value,
            total_price=contract.value
        )

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        formset = ContractItemFormSet(request.POST, instance=contract)
        
        if form.is_valid() and formset.is_valid():
            contract = form.save(commit=False)
            formset.save()
            
            # Recalculate total value
            total_value = sum(item.total_price for item in contract.items.all())
            contract.value = total_value
            contract.save()
            
            messages.success(request, 'Contrato atualizado com sucesso.')
            return redirect('comercial:contract_detail', pk=contract.pk)
    else:
        form = ContractForm(instance=contract)
        formset = ContractItemFormSet(instance=contract)
        
    return render(request, 'comercial/contract_form_fixed.html', {
        'contract': contract,
        'form': form,
        'formset': formset,
    })

@login_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contrato excluído com sucesso.')
        return redirect('comercial:contract_list')
        
    return render(request, 'comercial/contract_confirm_delete.html', {'contract': contract})

@login_required
def contract_template_list(request):
    templates = ContractTemplate.objects.all().order_by('name')
    return render(request, 'comercial/contract_template_list.html', {'templates': templates})

@login_required
def contract_template_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        template_type = request.POST.get('template_type')
        content = request.POST.get('content')
        
        ContractTemplate.objects.create(
            name=name,
            template_type=template_type,
            content=content
        )
        messages.success(request, 'Modelo de contrato criado com sucesso.')
        return redirect('comercial:contract_template_list')
        
    return render(request, 'comercial/contract_template_form_fixed.html')

@login_required
def contract_template_update(request, pk):
    template = get_object_or_404(ContractTemplate, pk=pk)
    
    if request.method == 'POST':
        template.name = request.POST.get('name')
        template.template_type = request.POST.get('template_type')
        template.content = request.POST.get('content')
        template.save()
        
        messages.success(request, 'Modelo de contrato atualizado com sucesso.')
        return redirect('comercial:contract_template_list')
        
    return render(request, 'comercial/contract_template_form_fixed.html', {'template': template})

from django.db.models import ProtectedError

@login_required
def contract_template_delete(request, pk):
    template = get_object_or_404(ContractTemplate, pk=pk)
    
    if request.method == 'POST':
        try:
            template.delete()
            messages.success(request, 'Modelo de contrato excluído com sucesso.')
        except ProtectedError:
            messages.error(request, 'Não é possível excluir este modelo pois existem contratos vinculados a ele.')
        return redirect('comercial:contract_template_list')
        
    return render(request, 'comercial/contract_template_confirm_delete.html', {'template': template})

@login_required
def contract_pdf(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    # Prepare content with substitutions
    content = replace_contract_variables(contract.template.content, contract)
    
    template_path = 'comercial/contract_pdf.html'
    context = {'contract': contract, 'content': content}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{contract.id}.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def contract_send_email(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    # Generate PDF
    # Prepare content with substitutions
    content = replace_contract_variables(contract.template.content, contract)
    
    template_path = 'comercial/contract_pdf.html'
    context = {'contract': contract, 'content': content}
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF in memory
    pdf_file = ContentFile(b'')
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)
    
    if pisa_status.err:
        messages.error(request, 'Erro ao gerar PDF para envio.')
        return redirect('comercial:contract_detail', pk=pk)
        
    # Send Email
    subject = f'Contrato #{contract.id} - Descartex'
    body = f"""
    Olá {contract.client.name},
    
    Segue em anexo o contrato #{contract.id} assinado.
    
    Atenciosamente,
    Equipe Descartex
    """
    
    email = EmailMessage(
        subject,
        body,
        'vendas@descartex.com.br', # Sender
        [contract.client.email or 'cliente@exemplo.com'], # Recipient (fallback if no email)
        bcc=['vendas@descartex.com.br'] # Copy to sender
    )
    
    # Get PDF content from the ContentFile
    pdf_content = pdf_file.file.getvalue()
    email.attach(f'contrato_{contract.id}.pdf', pdf_content, 'application/pdf')
    
    try:
        email.send()
        messages.success(request, f'Contrato enviado para {contract.client.email or "cliente@exemplo.com"} com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao enviar e-mail: {str(e)}')
        
    return redirect('comercial:contract_detail', pk=pk)

@login_required
def budget_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    budgets = Budget.objects.all().order_by('-created_at')
    
    if search_query:
        budgets = budgets.filter(
            Q(client__name__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(id__icontains=search_query)
        )
        
    if status_filter:
        budgets = budgets.filter(status=status_filter)
        
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comercial/budget_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter
    })

@login_required
def budget_create(request):
    if request.method == 'POST':
        client_id = request.POST.get('client')
        client = get_object_or_404(Person, pk=client_id)
        
        budget = Budget.objects.create(
            client=client,
            title=request.POST.get('title'),
            seller=request.user,
            date=request.POST.get('date'),
            validity_date=request.POST.get('validity_date'),
            payment_method=request.POST.get('payment_method'),
            payment_details=request.POST.get('payment_details'),
            observation=request.POST.get('observation'),
            address=request.POST.get('address'),
            contact=request.POST.get('contact'),
            status='Aberto',
            followup_strategy=request.POST.get('followup_strategy', 'Manual')
        )

        # Process Products
        product_ids = request.POST.getlist('product_id[]')
        product_quantities = request.POST.getlist('product_qty[]')
        product_prices = request.POST.getlist('product_price[]')
        
        total_value = 0

        for i in range(len(product_ids)):
            if product_ids[i]:
                qty = int(product_quantities[i])
                price = float(product_prices[i])
                BudgetProduct.objects.create(
                    budget=budget,
                    product_id=product_ids[i],
                    quantity=qty,
                    unit_price=price,
                    total_price=qty * price
                )
                total_value += qty * price

        # Process Services
        service_ids = request.POST.getlist('service_id[]')
        service_quantities = request.POST.getlist('service_qty[]')
        service_prices = request.POST.getlist('service_price[]')

        for i in range(len(service_ids)):
            if service_ids[i]:
                qty = int(service_quantities[i])
                price = float(service_prices[i])
                BudgetService.objects.create(
                    budget=budget,
                    service_id=service_ids[i],
                    quantity=qty,
                    unit_price=price,
                    total_price=qty * price
                )
                total_value += qty * price
        
        budget.total_value = total_value
        budget.save()

        messages.success(request, 'Orçamento criado com sucesso.')
        return redirect('comercial:budget_detail', pk=budget.pk)
        
    clients = Person.objects.filter(is_client=True, active=True)
    products = Product.objects.filter(active=True)
    services = Service.objects.filter(active=True)
    return render(request, 'comercial/budget_form.html', {
        'clients': clients,
        'products': products,
        'services': services
    })

@login_required
def budget_update(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        budget.title = request.POST.get('title')
        budget.date = request.POST.get('date')
        budget.validity_date = request.POST.get('validity_date')
        budget.payment_method = request.POST.get('payment_method')
        budget.payment_details = request.POST.get('payment_details')
        budget.observation = request.POST.get('observation')
        budget.address = request.POST.get('address')
        budget.address = request.POST.get('address')
        budget.contact = request.POST.get('contact')
        budget.followup_strategy = request.POST.get('followup_strategy')
        
        client_id = request.POST.get('client')
        if client_id:
            budget.client = get_object_or_404(Person, pk=client_id)
            
        # Clear existing items
        budget.products.all().delete()
        budget.services.all().delete()
        
        total_value = 0

        # Process Products
        product_ids = request.POST.getlist('product_id[]')
        product_quantities = request.POST.getlist('product_qty[]')
        product_prices = request.POST.getlist('product_price[]')
        
        for i in range(len(product_ids)):
            if product_ids[i]:
                qty = int(product_quantities[i])
                price = float(product_prices[i])
                BudgetProduct.objects.create(
                    budget=budget,
                    product_id=product_ids[i],
                    quantity=qty,
                    unit_price=price,
                    total_price=qty * price
                )
                total_value += qty * price

        # Process Services
        service_ids = request.POST.getlist('service_id[]')
        service_quantities = request.POST.getlist('service_qty[]')
        service_prices = request.POST.getlist('service_price[]')

        for i in range(len(service_ids)):
            if service_ids[i]:
                qty = int(service_quantities[i])
                price = float(service_prices[i])
                BudgetService.objects.create(
                    budget=budget,
                    service_id=service_ids[i],
                    quantity=qty,
                    unit_price=price,
                    total_price=qty * price
                )
                total_value += qty * price
                
        budget.total_value = total_value
        budget.save()

        messages.success(request, 'Orçamento atualizado com sucesso.')
        return redirect('comercial:budget_detail', pk=budget.pk)
        
    clients = Person.objects.filter(is_client=True, active=True)
    products = Product.objects.filter(active=True)
    services = Service.objects.filter(active=True)
    return render(request, 'comercial/budget_form.html', {
        'budget': budget, 
        'clients': clients,
        'products': products,
        'services': services
    })

@login_required
def budget_detail(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    return render(request, 'comercial/budget_detail.html', {'budget': budget})

@login_required
def budget_win(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    budget.status = 'Ganho'
    budget.save()
    messages.success(request, 'Orçamento marcado como Ganho!')
    return redirect('comercial:budget_detail', pk=pk)

@login_required
def budget_refuse(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    budget.status = 'Perdido'
    budget.save()
    messages.warning(request, 'Orçamento marcado como Perdido.')
    return redirect('comercial:budget_detail', pk=pk)

@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Orçamento excluído com sucesso.')
        return redirect('comercial:budget_list')
        
    return render(request, 'comercial/budget_confirm_delete.html', {'budget': budget})

@login_required
def budget_pdf(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    template_path = 'comercial/budget_pdf.html'
    context = {'budget': budget}
    response = HttpResponse(content_type='application/pdf')
    
    # Filename format: ClientName_DDMMYYYY.pdf
    client_slug = slugify(budget.client.name).replace('-', '_')
    date_str = budget.date.strftime('%d%m%Y') if budget.date else timezone.now().strftime('%d%m%Y')
    filename = f"{client_slug}_{date_str}.pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def budget_send_email(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    # Generate PDF
    template_path = 'comercial/budget_pdf.html'
    context = {'budget': budget}
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF in memory
    pdf_file = ContentFile(b'')
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)
    
    if pisa_status.err:
        messages.error(request, 'Erro ao gerar PDF para envio.')
        return redirect('comercial:budget_detail', pk=pk)
        
    # Send Email
    subject = f'Orçamento #{budget.id:06d} - Descartex'
    body = f"""
    Olá {budget.client.name},
    
    Segue em anexo o orçamento #{budget.id:06d} conforme solicitado.
    
    Atenciosamente,
    Equipe Descartex
    """
    
    email = EmailMessage(
        subject,
        body,
        'vendas@descartex.com.br', # Sender
        [budget.client.email or 'cliente@exemplo.com'], # Recipient (fallback if no email)
        bcc=['vendas@descartex.com.br'] # Copy to sender
    )
    
    # Get PDF content from the ContentFile
    pdf_content = pdf_file.file.getvalue()
    email.attach(f'orcamento_{budget.id}.pdf', pdf_content, 'application/pdf')
    
    try:
        email.send()
        budget.last_followup = timezone.now()
        budget.save()
        messages.success(request, f'Orçamento enviado para {budget.client.email or "cliente@exemplo.com"} com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao enviar e-mail: {str(e)}')
        
    return redirect('comercial:budget_detail', pk=pk)

@login_required
def sales_actions(request):
    # Filter budgets: Status 'Aberto' AND Date <= 7 days ago
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    
    pending_budgets = Budget.objects.filter(
        status='Aberto',
        date__lte=seven_days_ago
    ).order_by('date')
    
    manual_budgets = pending_budgets.filter(followup_strategy='Manual')
    automatic_budgets = pending_budgets.filter(followup_strategy='Automatico')
    
    return render(request, 'comercial/sales_actions.html', {
        'manual_budgets': manual_budgets,
        'automatic_budgets': automatic_budgets
    })

@login_required
def toggle_followup_strategy(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if budget.followup_strategy == 'Manual':
        budget.followup_strategy = 'Automatico'
    else:
        budget.followup_strategy = 'Manual'
    budget.save()
    messages.success(request, f'Estratégia do orçamento #{budget.id} alterada para {budget.followup_strategy}.')
    return redirect('comercial:sales_actions')

@login_required
def service_list(request):
    search_query = request.GET.get('search', '')
    
    services = Service.objects.all().order_by('name')
    
    if search_query:
        services = services.filter(name__icontains=search_query)
        
    paginator = Paginator(services, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comercial/service_list.html', {'page_obj': page_obj, 'search_query': search_query})
    
@login_required
def billing_group_list(request):
    billing_groups = BillingGroup.objects.all().order_by('name')
    return render(request, 'comercial/billing_group_list.html', {'billing_groups': billing_groups})

@login_required
@login_required
def billing_group_create(request):
    if request.method == 'POST':
        form = BillingGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de faturamento criado com sucesso.')
            return redirect('comercial:billing_group_list')
    else:
        form = BillingGroupForm()
        
    return render(request, 'comercial/billing_group_form.html', {'form': form})

@login_required
@login_required
def billing_group_update(request, pk):
    group = get_object_or_404(BillingGroup, pk=pk)
    
    if request.method == 'POST':
        form = BillingGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de faturamento atualizado com sucesso.')
            return redirect('comercial:billing_group_list')
    else:
        form = BillingGroupForm(instance=group)
        
    return render(request, 'comercial/billing_group_form.html', {'form': form})

@login_required
def billing_group_delete(request, pk):
    group = get_object_or_404(BillingGroup, pk=pk)
    
    if request.method == 'POST':
        try:
            group.delete()
            messages.success(request, 'Grupo de faturamento excluído com sucesso.')
        except ProtectedError:
            messages.error(request, 'Não é possível excluir este grupo pois existem contratos vinculados a ele.')
        return redirect('comercial:billing_group_list')
        
    return render(request, 'comercial/billing_group_confirm_delete.html', {'object': group})

@login_required
def service_create(request):
    if request.method == 'POST':
        Service.objects.create(
            name=request.POST.get('name'),
            base_cost=request.POST.get('base_cost'),
            sale_price=request.POST.get('sale_price')
        )
        messages.success(request, 'Serviço criado com sucesso.')
        return redirect('comercial:service_list')
    
    return render(request, 'comercial/service_form.html')

@login_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.base_cost = request.POST.get('base_cost')
        service.sale_price = request.POST.get('sale_price')
        service.save()
        
        messages.success(request, 'Serviço atualizado com sucesso.')
        return redirect('comercial:service_list')
        
    return render(request, 'comercial/service_form.html', {'service': service})

@login_required
def run_billing(request):
    out = io.StringIO()
    call_command('processar_contratos', stdout=out)
    result = out.getvalue()
    messages.info(request, f'Resultado do Faturamento: {result}')
    return redirect('comercial:contract_list')

@login_required
def get_client_details(request, pk):
    client = get_object_or_404(Person, pk=pk)
    
    address_parts = []
    if client.address: address_parts.append(client.address)
    if client.number: address_parts.append(client.number)
    if client.neighborhood: address_parts.append(client.neighborhood)
    if client.city: address_parts.append(client.city)
    if client.state: address_parts.append(client.state)
    if client.zip_code: address_parts.append(f'CEP: {client.zip_code}')
    full_address = ', '.join(address_parts)

    data = {
        'name': client.name,
        'document': client.document,
        'address': full_address,
        'responsible_name': client.responsible_name,
        'responsible_cpf': client.responsible_cpf,
        'email': client.email,
        'phone': client.phone
    }
    return JsonResponse(data)

@login_required
def get_contract_template_details(request, pk):
    template = get_object_or_404(ContractTemplate, pk=pk)
    return JsonResponse({'content': template.content})




