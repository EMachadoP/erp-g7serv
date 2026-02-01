from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import Person, Service, CompanySettings
from .utils import MENU_PERMISSIONS

def is_socio_diretor(user):
    return user.is_superuser or user.groups.filter(name='SÓCIO-DIRETOR').exists()

from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from ai_core.models import AtendimentoAI
from operacional.models import ServiceOrder
from comercial.models import Person, Contract
from financeiro.models import AccountPayable

@login_required
def home(request):
    # Redirect to dashboard as it's the new standard entry point
    return redirect('core:dashboard')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        mes_atual = timezone.now().month
        ano_atual = timezone.now().year

        # Métricas Dashboard BI
        context['total_clientes'] = Person.objects.filter(is_client=True).count()
        
        # Faturamento do Mês
        faturamento = Contract.objects.filter(
            created_at__month=mes_atual, 
            created_at__year=ano_atual,
            status='Ativo'
        ).aggregate(total=Sum('value'))['total'] or 0
        context['faturamento_mes'] = faturamento

        # Operacional
        context['os_pendentes'] = ServiceOrder.objects.filter(status='PENDING').count()
        context['os_andamento'] = ServiceOrder.objects.filter(status='IN_PROGRESS').count()

        # Financeiro
        context['contas_vencer'] = AccountPayable.objects.filter(
            status='PENDING', 
            due_date__gte=hoje
        ).count()

        # AI Triage
        context['atendimentos_hoje'] = AtendimentoAI.objects.filter(timestamp__date=hoje).count()
        context['ultimos_atendimentos'] = AtendimentoAI.objects.order_by('-timestamp')[:5]

        # Pizza Charts Data (Compatibility)
        context['ai_comercial'] = AtendimentoAI.objects.filter(categoria_detectada='orcamento').count()
        context['ai_suporte'] = AtendimentoAI.objects.filter(categoria_detectada='suporte').count()
        context['ai_financeiro'] = AtendimentoAI.objects.filter(categoria_detectada='financeiro').count()
        context['ai_outros'] = AtendimentoAI.objects.filter(categoria_detectada='outro').count()
        
        context['os_pendente'] = context['os_pendentes']
        context['os_andamento'] = context['os_andamento']
        context['os_concluida'] = ServiceOrder.objects.filter(status='COMPLETED').count()

        return context

# --- User Management ---

@login_required
@user_passes_test(is_socio_diretor)
def user_list(request):
    search_query = request.GET.get('search', '')
    show_inactive = request.GET.get('show_inactive', 'off')
    
    users = User.objects.all().order_by('username')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query)
        )
        
    if show_inactive != 'on':
        users = users.filter(is_active=True)
        
    return render(request, 'core/user_list_v2.html', {
        'users': users,
        'search_query': search_query,
        'show_inactive': show_inactive,
        'checked_attribute': 'checked' if show_inactive == 'on' else ''
    })

@login_required
@user_passes_test(is_socio_diretor)
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        group_id = request.POST.get('group')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.save()
            
            if group_id:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
                
            messages.success(request, 'Usuário criado com sucesso.')
            return redirect('core:user_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {e}')
            
    groups = Group.objects.all()
    return render(request, 'core/user_form_v2.html', {'groups': groups})

@login_required
@user_passes_test(is_socio_diretor)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            
        user.save()
        
        # Update Group
        user.groups.clear()
        group_id = request.POST.get('group')
        if group_id:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            
        messages.success(request, 'Usuário atualizado com sucesso.')
        return redirect('core:user_list')
        
    groups = Group.objects.all()
    user_group = user.groups.first()
    return render(request, 'core/user_form_v2.html', {'user_obj': user, 'groups': groups, 'user_group': user_group})

# --- Profile (Group) Management ---

@login_required
@user_passes_test(is_socio_diretor)
def profile_list(request):
    groups = Group.objects.all().order_by('name')
    return render(request, 'core/profile_list.html', {'groups': groups})

def get_permissions_from_mapping():
    """
    Returns a list of permissions based on the MENU_PERMISSIONS mapping.
    """
    mapped_permissions = []
    
    for menu in MENU_PERMISSIONS:
        menu_item = {
            'name': menu['name'],
            'submenus': []
        }
        
        if 'submenus' in menu:
            for submenu in menu['submenus']:
                perm_str = submenu['perm']
                app_label, codename = perm_str.split('.')
                # We want to get all permissions for this model (view, add, change, delete)
                # Assuming the codename is like 'view_modelname'
                action, model_name = codename.split('_', 1)
                
                perms = Permission.objects.filter(
                    content_type__app_label=app_label,
                    content_type__model=model_name
                )
                
                # Translate permission names
                perms_list = []
                for perm in perms:
                    if perm.name.startswith('Can add '):
                        perm.name = perm.name.replace('Can add ', 'Adicionar ')
                    elif perm.name.startswith('Can change '):
                        perm.name = perm.name.replace('Can change ', 'Editar ')
                    elif perm.name.startswith('Can delete '):
                        perm.name = perm.name.replace('Can delete ', 'Excluir ')
                    elif perm.name.startswith('Can view '):
                        perm.name = perm.name.replace('Can view ', 'Visualizar ')
                    perms_list.append(perm)
                
                menu_item['submenus'].append({
                    'name': submenu['name'],
                    'perms': perms_list
                })
        else:
            # Top level menu item
            perm_str = menu['perm']
            app_label, codename = perm_str.split('.')
            action, model_name = codename.split('_', 1)
            
            perms = Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model_name
            )
            
            # Translate permission names
            perms_list = []
            for perm in perms:
                if perm.name.startswith('Can add '):
                    perm.name = perm.name.replace('Can add ', 'Adicionar ')
                elif perm.name.startswith('Can change '):
                    perm.name = perm.name.replace('Can change ', 'Editar ')
                elif perm.name.startswith('Can delete '):
                    perm.name = perm.name.replace('Can delete ', 'Excluir ')
                elif perm.name.startswith('Can view '):
                    perm.name = perm.name.replace('Can view ', 'Visualizar ')
                perms_list.append(perm)
            
            menu_item['submenus'].append({
                'name': menu['name'], # Treat as single submenu
                'perms': perms_list
            })
            
        mapped_permissions.append(menu_item)
        
    return mapped_permissions

@login_required
@user_passes_test(is_socio_diretor)
def profile_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        group = Group.objects.create(name=name)
        group.permissions.set(permission_ids)
        
        messages.success(request, 'Perfil criado com sucesso.')
        return redirect('core:profile_list')
        
    grouped_permissions = get_permissions_from_mapping()
    return render(request, 'core/profile_form_v2.html', {
        'grouped_permissions': grouped_permissions,
        'current_permissions': []
    })

@login_required
@user_passes_test(is_socio_diretor)
def profile_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        group.name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        group.save()
        group.permissions.set(permission_ids)
        
        messages.success(request, 'Perfil atualizado com sucesso.')
        return redirect('core:profile_list')
        
    grouped_permissions = get_permissions_from_mapping()
    current_permissions = group.permissions.values_list('id', flat=True)
    
    return render(request, 'core/profile_form_v2.html', {
        'group': group, 
        'grouped_permissions': grouped_permissions,
        'current_permissions': current_permissions
    })

@login_required
@user_passes_test(is_socio_diretor)
def user_change_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password and password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, 'Senha alterada com sucesso.')
            return redirect('core:user_list')
        else:
            messages.error(request, 'As senhas não conferem.')
            
    return render(request, 'core/user_change_password.html', {'user_obj': user})

@login_required
@user_passes_test(is_socio_diretor)
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    # Prevent deactivating self
    if user == request.user:
        messages.error(request, 'Você não pode inativar seu próprio usuário.')
        return redirect('core:user_list')
        
    user.is_active = not user.is_active
    user.save()
    status = "ativado" if user.is_active else "inativado"
    messages.success(request, f'Usuário {user.username} {status} com sucesso.')
    return redirect('core:user_list')

@login_required
@user_passes_test(is_socio_diretor)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Você não pode remover seu próprio usuário.')
        return redirect('core:user_list')
        
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Usuário removido com sucesso.')
        return redirect('core:user_list')
        
    return render(request, 'core/user_confirm_delete.html', {'user_obj': user})

# --- Technician Management ---
from .models import Technician
from .forms import TechnicianForm

@login_required
@user_passes_test(is_socio_diretor)
def technician_list(request):
    technicians = Technician.objects.all().order_by('user__first_name')
    return render(request, 'core/technician_list.html', {'technicians': technicians})

@login_required
@user_passes_test(is_socio_diretor)
def technician_create(request):
    if request.method == 'POST':
        form = TechnicianForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Técnico cadastrado com sucesso.')
            return redirect('core:technician_list')
    else:
        form = TechnicianForm()
    return render(request, 'core/technician_form.html', {'form': form, 'title': 'Novo Técnico'})

@login_required
@user_passes_test(is_socio_diretor)
def technician_update(request, pk):
    technician = get_object_or_404(Technician, pk=pk)
    if request.method == 'POST':
        form = TechnicianForm(request.POST, instance=technician, user_instance=technician.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Técnico atualizado com sucesso.')
            return redirect('core:technician_list')
    else:
        form = TechnicianForm(instance=technician, user_instance=technician.user)
    return render(request, 'core/technician_form.html', {'form': form, 'title': 'Editar Técnico'})
