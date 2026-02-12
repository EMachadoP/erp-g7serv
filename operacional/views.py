from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.core.files.base import ContentFile
import base64
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .services.pdf_service import render_preventive_pdf
from .services.email_service import send_checklist_email
from .models import ServiceOrder, ServiceOrderItem, OSAnexo, ChecklistCategoria, ChecklistPergunta, ChecklistResposta
from .forms import ServiceOrderItemFormSet, ServiceOrderForm, ServiceOrderItemForm
from core.models import Person, CompanySettings
from django.core.paginator import Paginator
from estoque.models import Product, StockMovement
from comercial.models import Budget, Contract
from django.contrib.auth.models import User
import io
from xhtml2pdf import pisa

@login_required
def service_order_checklist_pdf(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    categories = ChecklistCategoria.objects.prefetch_related('perguntas').all()
    responses = {r.pergunta_id: r for r in ChecklistResposta.objects.filter(os=order)}
    
    return render_preventive_pdf(order, categories, responses)

@login_required
def service_order_checklist_email(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    categories = ChecklistCategoria.objects.prefetch_related('perguntas').all()
    responses = {r.pergunta_id: r for r in ChecklistResposta.objects.filter(os=order)}
    
    success, message = send_checklist_email(order, categories, responses)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('operacional:service_order_detail', pk=order.id)

@login_required
def service_order_list(request):
    # ... existing implementation ...
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    orders = ServiceOrder.objects.select_related('client').all().order_by('-created_at')
    
    if search_query:
        if search_query.isdigit():
            orders = orders.filter(id=int(search_query))
        else:
            orders = orders.filter(
                Q(client__name__icontains=search_query) |
                Q(client__fantasy_name__icontains=search_query) |
                Q(product__icontains=search_query)
            )
        
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    if date_filter:
        orders = orders.filter(Q(scheduled_date__date=date_filter) | Q(created_at__date=date_filter))
        
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'operacional/service_order_list.html', {
        'page_obj': page_obj, 
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': ServiceOrder.STATUS_CHOICES
    })

@login_required
def service_order_cancel(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    # We only allow canceling if it's not already completed or canceled
    if order.status not in ['COMPLETED', 'CANCELED']:
        order.status = 'CANCELED'
        order.save()
        messages.success(request, f'Ordem de Serviço #{order.id} cancelada com sucesso.')
    else:
        messages.warning(request, f'Não é possível cancelar uma OS com status {order.get_status_display()}.')
        
    return redirect('operacional:service_order_list')

@login_required
def service_order_detail(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    return render(request, 'operacional/service_order_detail.html', {'order': order})

@login_required
def service_order_create(request):
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST)
        formset = ServiceOrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            
            # Manual fields
            order.start_date = request.POST.get('start_date') or None
            order.end_date = request.POST.get('end_date') or None
            order.value = request.POST.get('value') or 0
            order.order_type = request.POST.get('order_type')
            order.reason = request.POST.get('reason')
            order.duration = request.POST.get('duration')
            order.address = request.POST.get('address')
            order.contact = request.POST.get('contact')
            
            order.save()
            
            formset.instance = order
            formset.save()
            
            # Update total value based on items
            total_items = sum(item.total_price for item in order.items.all())
            if total_items > 0:
                order.value = total_items
                order.save()

            messages.success(request, 'Ordem de Serviço criada com sucesso.')
            return redirect('operacional:service_order_detail', pk=order.id)
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    
    else:
        form = ServiceOrderForm()
        formset = ServiceOrderItemFormSet()

    clients = Person.objects.filter(is_client=True, is_supplier=False)
    
    return render(request, 'operacional/service_order_form.html', {
        'form': form,
        'clients': clients,
        'type_choices': ServiceOrder.TYPE_CHOICES,
        'reason_choices': ServiceOrder.REASON_CHOICES,
        'formset': formset
    })

@login_required
def service_order_update(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST, instance=order)
        formset = ServiceOrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            
            # Manual fields
            order.start_date = request.POST.get('start_date') or None
            order.end_date = request.POST.get('end_date') or None
            order.value = request.POST.get('value') or 0
            order.order_type = request.POST.get('order_type')
            order.reason = request.POST.get('reason')
            order.duration = request.POST.get('duration')
            order.address = request.POST.get('address')
            order.contact = request.POST.get('contact')
            
            order.save()
            formset.save()
            
            # Update total value
            total_items = sum(item.total_price for item in order.items.all())
            if total_items > 0:
                order.value = total_items
                order.save()
            
            messages.success(request, 'Ordem de Serviço atualizada com sucesso.')
            return redirect('operacional:service_order_detail', pk=order.id)
        else:
             messages.error(request, 'Erro no formulário. Verifique os dados.')
            
    else:
        form = ServiceOrderForm(instance=order)
        formset = ServiceOrderItemFormSet(instance=order)

    clients = Person.objects.filter(is_client=True, is_supplier=False)
    
    return render(request, 'operacional/service_order_form.html', {
        'form': form,
        'order': order,
        'clients': clients,
        'type_choices': ServiceOrder.TYPE_CHOICES,
        'reason_choices': ServiceOrder.REASON_CHOICES,
        'formset': formset
    })

@login_required
def operational_progress(request):
    # Column 1: Liberação de Orçamento
    # Budgets that are 'Ganho' but NOT yet approved by operations
    budgets_to_approve = Budget.objects.filter(status='Ganho', approved_by_operations=False)

    # Column 2: Orçamentos Pendentes de Contrato
    # Budgets 'Ganho', Approved, have Services, but NO Contract linked
    # We check if budget has services (BudgetService exists)
    budgets_pending_contract = Budget.objects.filter(
        status='Ganho', 
        approved_by_operations=True, 
        services__isnull=False, 
        contract__isnull=True
    ).distinct()

    # Column 3: Orçamentos Pendentes de OS
    # Budgets 'Ganho', Approved, have Products OR Services, but NO ServiceOrder linked
    # (Note: A budget might need BOTH Contract and OS if it has services. 
    #  Or maybe OS is for one-time services/products and Contract for recurring?
    #  For now, let's assume if it has products/services and no OS, it needs one.)
    # Column 3: Orçamentos Pendentes de OS
    budgets_pending_os = Budget.objects.filter(
        status='Ganho', 
        approved_by_operations=True, 
        service_orders__isnull=True
    ).filter(
        Q(products__isnull=False) | Q(services__isnull=False)
    ).distinct()

    # --- NEW DASHBOARD COLUMNS AS REQUESTED ---
    
    # 1. Pendentes OS (Aberto ou Agendado -> PENDING)
    # The user asked for 'OPEN' or 'SCHEDULED'. Our model has 'PENDING'.
    # We will treat PENDING as the bucket for these.
    # If we had a separate SCHEDULED status, we would use Q(status='PENDING') | Q(status='SCHEDULED')
    pendentes_os = ServiceOrder.objects.filter(status='PENDING').select_related('client', 'technician').order_by('scheduled_date')

    # 2. Em Execução (IN_PROGRESS)
    em_execucao = ServiceOrder.objects.filter(status='IN_PROGRESS').select_related('client', 'technician').order_by('scheduled_date')

    # 3. Aguardando Material (WAITING_MATERIAL)
    aguardando_material = ServiceOrder.objects.filter(status='WAITING_MATERIAL').select_related('client', 'technician').order_by('scheduled_date')

    # 4. Concluídas Hoje (COMPLETED with checkout_today)
    today = timezone.now().date()
    concluidas_hoje = ServiceOrder.objects.filter(
        status='COMPLETED', 
        checkout_time__date=today
    ).select_related('client', 'technician').order_by('-checkout_time')

    # Selected OS highlighting logic
    selected_os_id = request.GET.get('os_id')
    selected_os = None
    if selected_os_id:
        selected_os = ServiceOrder.objects.filter(pk=selected_os_id).first()

    return render(request, 'operacional/operational_dashboard.html', {
        'budgets_to_approve': budgets_to_approve,
        'budgets_pending_contract': budgets_pending_contract,
        'budgets_pending_os': budgets_pending_os,
        
        # New Context Variables
        'pendentes_os': pendentes_os,
        'em_execucao': em_execucao,
        'aguardando_material': aguardando_material,
        'concluidas_hoje': concluidas_hoje,
        
        # Legacy/Extra context if needed (removed os_in_progress duplicate)
        'now': timezone.now(), 
        'selected_os': selected_os,
    })

@login_required
def approve_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    budget.approved_by_operations = True
    budget.save()
    messages.success(request, f'Orçamento #{budget.id} liberado pelo operacional.')
    return redirect('operacional:operational_progress')

@login_required
def refuse_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    # If refused, maybe send back to 'Aberto' so Commercial can adjust?
    budget.status = 'Aberto'
    budget.approved_by_operations = False
    budget.save()
    messages.warning(request, f'Orçamento #{budget.id} recusado e retornado para "Aberto".')
    return redirect('operacional:operational_progress')

@login_required
def create_os_from_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    # Create OS based on Budget
    # We can aggregate products/services into the description
    description_parts = []
    total_value = budget.total_value
    
    for bp in budget.products.all():
        description_parts.append(f"Produto: {bp.product.name} (Qtd: {bp.quantity})")
        
    for bs in budget.services.all():
        description_parts.append(f"Serviço: {bs.service.name} (Qtd: {bs.quantity})")
        
    full_description = "\n".join(description_parts)
    if budget.observation:
        full_description += f"\n\nObs: {budget.observation}"

    os = ServiceOrder.objects.create(
        client=budget.client,
        budget=budget,
        product=budget.title or "Orçamento #" + str(budget.id),
        description=full_description,
        value=total_value,
        status='PENDING',
        start_date=budget.date # Default to budget date or today?
    )
    
    messages.success(request, f'OS #{os.id} criada a partir do Orçamento #{budget.id}.')
    return redirect('operacional:service_order_detail', pk=os.id)

@login_required
def service_order_mobile(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        signature_data = request.POST.get('signature_data')
        
        if status:
            order.status = status
            
        if signature_data:
            format, imgstr = signature_data.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name=f'signature_os_{order.id}.{ext}')
            order.signature_image = data
            
        order.save()
        messages.success(request, 'OS atualizada com sucesso via Mobile.')
        return redirect('operacional:service_order_list')
        
    return render(request, 'operacional/service_order_mobile.html', {'order': order})

@login_required
def service_order_finish_mobile(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        solution = request.POST.get('solution')
        
        if signature_data:
            format, imgstr = signature_data.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name=f'signature_os_{order.id}.{ext}')
            order.signature_image = data
            order.solution = solution
            order.status = 'COMPLETED'
            order.checkout_time = timezone.now()
            order.save()
            
            messages.success(request, 'OS Finalizada com Sucesso!')
            return redirect('operacional:mobile_os_list')
            
    return render(request, 'operacional/mobile_os_finish.html', {'order': order})

@login_required
def service_order_pdf(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    template_path = 'operacional/service_order_pdf.html'
    context = {'order': order}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="os_{order.id}.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


# ==========================================
# MOBILE / FIELD TECHNICIAN VIEWS
# ==========================================

@login_required
def mobile_os_list(request):
    """
    List active OS for the logged-in technician. 
    Shows all if superuser.
    """
    from django.db.models import Q # Ensure Q is imported locally if not global

    tecnico_user = request.user
    # Status que devem aparecer (TODOS os pendentes/ativos)
    # Mapping 'OPEN', 'SCHEDULED' -> 'PENDING'
    status_visiveis = ['PENDING', 'IN_PROGRESS', 'WAITING_MATERIAL', 'OPEN', 'SCHEDULED']

    if request.user.is_superuser:
        os_list = ServiceOrder.objects.exclude(status__in=['COMPLETED', 'CANCELED']).order_by('-scheduled_date', '-id')
    else:
        # Busca abrangente (Case-insensitive para capturar AndreBezerra vs andrebezerra)
        os_list = ServiceOrder.objects.filter(
            technician__username__iexact=tecnico_user.username,
            status__in=status_visiveis
        ).order_by('-scheduled_date', '-id')

    # Debug Print to Terminal
    debug_msg = f"Usuário: {request.user} (ID: {request.user.id}, Super: {request.user.is_superuser}) - OSs encontradas: {os_list.count()}"
    print(debug_msg)
    
    # Write to a file we can read
    import os as py_os
    with open("debug_view_mobile.log", "a") as f:
        from django.utils import timezone
        f.write(f"[{timezone.now()}] {debug_msg}\n")

    return render(request, 'operacional/mobile_os_list.html', {'os_list': os_list})

@login_required
def mobile_os_detail(request, pk):
    os = get_object_or_404(ServiceOrder, pk=pk)
    return render(request, 'operacional/mobile_os_detail.html', {'os': os})

@csrf_exempt
@login_required
@require_POST
def api_checkin(request, pk):
    """
    Receives { lat: 123, long: 456 }
    Updates OS status to IN_PROGRESS and saves location.
    """
    print(f"DEBUG: Recebendo check-in para OS #{pk}")
    try:
        os = ServiceOrder.objects.get(pk=pk)
        data = json.loads(request.body)
        print(f"DEBUG: Dados recebidos: {data}")
        
        os.checkin_lat = data.get('lat')
        os.checkin_long = data.get('long')
        os.checkin_time = timezone.now()
        os.status = 'IN_PROGRESS'
        os.save()
        
        print(f"DEBUG: Check-in salvo com sucesso para OS #{pk}")
        return JsonResponse({'success': True, 'status': 'Em Execução', 'time': os.checkin_time.strftime('%H:%M')})
    except Exception as e:
        print(f"DEBUG: ERRO no check-in: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@login_required
@require_POST
def api_upload_photo(request, pk):
    """
    Receives file in request.FILES['photo'] and type in request.POST['type']
    """
    try:
        os = ServiceOrder.objects.get(pk=pk)
        photo = request.FILES.get('photo')
        photo_type = request.POST.get('type', 'Diagnostico')
        
        if not photo:
            return JsonResponse({'success': False, 'error': 'Nenhuma foto enviada.'}, status=400)
            
        anexo = OSAnexo.objects.create(
            os=os,
            file=photo,
            type=photo_type
        )
        
        return JsonResponse({
            'success': True, 
            'url': anexo.file.url, 
            'id': anexo.id,
            'type': anexo.get_type_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
@login_required
def checklist_mobile_view(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    categories = ChecklistCategoria.objects.prefetch_related('perguntas').all()
    
    # Pre-load existing responses
    responses = {r.pergunta_id: r for r in ChecklistResposta.objects.filter(os=order)}
    
    return render(request, 'operacional/checklist_mobile.html', {
        'order': order,
        'categories': categories,
        'responses': responses
    })

@csrf_exempt
@login_required
@require_POST
def save_checklist_api(request, pk):
    """
    Saves a single checklist response (answer, comment, or photo).
    """
    order = get_object_or_404(ServiceOrder, pk=pk)
    pergunta_id = request.POST.get('pergunta_id')
    value = request.POST.get('value')
    comment = request.POST.get('comment')
    photo = request.FILES.get('photo')
    
    resposta, created = ChecklistResposta.objects.get_or_create(
        os=order,
        pergunta_id=pergunta_id
    )
    
    if value is not None:
        resposta.resposta_valor = value
    if comment is not None:
        resposta.comentario = comment
    if photo:
        resposta.foto = photo
        
    resposta.save()
    
    return JsonResponse({
        'success': True,
        'resposta_id': resposta.id,
        'photo_url': resposta.foto.url if resposta.foto else None
    })

@csrf_exempt
@login_required
@require_POST
def finalize_checklist_api(request, pk):
    """
    Finalizes the checklist, captures signature if provided, and updates OS status.
    """
    order = get_object_or_404(ServiceOrder, pk=pk)
    signature_data = request.POST.get('signature_data')
    lat = request.POST.get('lat')
    lng = request.POST.get('lng')
    
    if signature_data:
        format, imgstr = signature_data.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name=f"signature_os_{order.id}.{ext}")
        order.signature_image = data
        
    if lat and lng:
        order.checkout_lat = lat # We might need to add this field or reuse checkin
        order.checkout_long = lng
        
    order.status = 'COMPLETED'
    order.checkout_time = timezone.now()
    order.save()
    
    return JsonResponse({'success': True})
