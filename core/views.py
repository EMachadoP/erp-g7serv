"""
Views do módulo core - ERP G7Serv
"""

import os  # <-- NO TOPO!

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.contenttypes.models import ContentType

# Imports de outros módulos
from ai_core.models import AtendimentoAI
from operacional.models import ServiceOrder
from comercial.models import Person, Contract
from financeiro.models import AccountPayable

# Imports locais
from .models import CompanySettings, Technician
from .forms import TechnicianForm


def is_socio_diretor(user):
    return user.is_superuser or user.groups.filter(name='SÓCIO-DIRETOR').exists()


@login_required
def home(request):
    return redirect('core:dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        hoje = timezone.now().date()
        mes_atual = timezone.now().month
        ano_atual = timezone.now().year

        context['total_clientes'] = Person.objects.filter(is_client=True).count()
        
        faturamento = Contract.objects.filter(
            created_at__month=mes_atual, 
            created_at__year=ano_atual,
            status='Ativo'
        ).aggregate(total=Sum('value'))['total'] or 0
        context['faturamento_mes'] = faturamento

        context['os_pendentes'] = ServiceOrder.objects.filter(status='PENDING').count()
        context['os_andamento'] = ServiceOrder.objects.filter(status='IN_PROGRESS').count()
        context['os_concluida'] = ServiceOrder.objects.filter(status='COMPLETED').count()

        context['contas_vencer'] = AccountPayable.objects.filter(
            status='PENDING', 
            due_date__gte=hoje
        ).count()

        context['atendimentos_hoje'] = AtendimentoAI.objects.filter(
            timestamp__date=hoje
        ).count()
        
        context['ultimos_atendimentos'] = AtendimentoAI.objects.order_by('-timestamp')[:5]

        context['ai_comercial'] = AtendimentoAI.objects.filter(
            categoria_detectada='orcamento'
        ).count()
        context['ai_suporte'] = AtendimentoAI.objects.filter(
            categoria_detectada='suporte'
        ).count()
        context['ai_financeiro'] = AtendimentoAI.objects.filter(
            categoria_detectada='financeiro'
        ).count()
        context['ai_outros'] = AtendimentoAI.objects.filter(
            categoria_detectada='outro'
        ).count()
        
        context['os_pendente'] = context['os_pendentes']

        return context


# ==============================================================================
# USUÁRIOS (mantido igual)
# ==============================================================================
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
        try:
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password')
            )
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.is_active = request.POST.get('is_active') == 'on'
            user.save()
            
            group_id = request.POST.get('group')
            if group_id:
                user.groups.add(Group.objects.get(id=group_id))
                
            messages.success(request, 'Usuário criado com sucesso.')
            return redirect('core:user_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {e}')
            
    return render(request, 'core/user_form_v2.html', {'groups': Group.objects.all()})


@login_required
@user_passes_test(is_socio_diretor)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            
        user.save()
        
        user.groups.clear()
        group_id = request.POST.get('group')
        if group_id:
            user.groups.add(Group.objects.get(id=group_id))
            
        messages.success(request, 'Usuário atualizado com sucesso.')
        return redirect('core:user_list')
        
    return render(request, 'core/user_form_v2.html', {
        'user_obj': user,
        'groups': Group.objects.all(),
        'user_group': user.groups.first()
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


# ==============================================================================
# PERFIS - VERSÃO SIMPLIFICADA E CORRIGIDA
# ==============================================================================
@login_required
@user_passes_test(is_socio_diretor)
def profile_list(request):
    groups = Group.objects.all().order_by('name')
    return render(request, 'core/profile_list.html', {'groups': groups})


def get_permissions_from_mapping():
    """
    Retorna permissões organizadas por app_label.
    Versão simplificada - não depende de MENU_PERMISSIONS.
    """
    try:
        permissions = Permission.objects.all().select_related('content_type')
        apps_permissions = {}
        
        for perm in permissions:
            try:
                if not perm.content_type:
                    continue
                    
                app = perm.content_type.app_label
                if app not in apps_permissions:
                    apps_permissions[app] = []
                
                # Traduz nome da permissão
                p_name = str(perm.name or '')
                if p_name.startswith('Can add '):
                    p_name = p_name.replace('Can add ', 'Adicionar ')
                elif p_name.startswith('Can change '):
                    p_name = p_name.replace('Can change ', 'Editar ')
                elif p_name.startswith('Can delete '):
                    p_name = p_name.replace('Can delete ', 'Excluir ')
                elif p_name.startswith('Can view '):
                    p_name = p_name.replace('Can view ', 'Visualizar ')
                
                perm.name = p_name
                apps_permissions[app].append(perm)
            except Exception as e:
                # Silently ignore one bad permission
                continue
        
        return apps_permissions
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro fatal em get_permissions_from_mapping: {e}", exc_info=True)
        return {}


@login_required
@user_passes_test(is_socio_diretor)
def profile_create(request):
    """Cria novo perfil/grupo."""
    if request.method == 'POST':
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
            return render(request, 'core/profile_form_v2.html', {
                'group': None,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': []
            })
        
        try:
            group = Group.objects.create(name=name)
            if permission_ids:
                group.permissions.set(permission_ids)
            messages.success(request, 'Perfil criado com sucesso.')
            return redirect('core:profile_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar perfil no banco: {e}')
    
    # GET - mostra formulário
    perms = get_permissions_from_mapping()
    return render(request, 'core/profile_form_v2.html', {
        'group': None,
        'apps_permissions': perms,
        'current_permissions': []
    })


@login_required
@user_passes_test(is_socio_diretor)
def profile_update(request, pk):
    """Atualiza perfil/grupo existente."""
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
            return render(request, 'core/profile_form_v2.html', {
                'group': group,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': list(group.permissions.values_list('id', flat=True))
            })
        
        try:
            group.name = name
            group.save()
            group.permissions.set(permission_ids)
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('core:profile_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar perfil no banco: {e}')
    
    # GET - mostra formulário
    # CORREÇÃO: Converte QuerySet para lista para funcionar com `in` no template
    current_permissions = list(group.permissions.values_list('id', flat=True))
    
    return render(request, 'core/profile_form_v2.html', {
        'group': group,
        'apps_permissions': get_permissions_from_mapping(),
        'current_permissions': current_permissions
    })


# ==============================================================================
# TÉCNICOS
# ==============================================================================
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
        
    return render(request, 'core/technician_form.html', {
        'form': form,
        'title': 'Novo Técnico'
    })


@login_required
@user_passes_test(is_socio_diretor)
def technician_update(request, pk):
    technician = get_object_or_404(Technician, pk=pk)
    
    if request.method == 'POST':
        form = TechnicianForm(
            request.POST,
            instance=technician,
            user_instance=technician.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Técnico atualizado com sucesso.')
            return redirect('core:technician_list')
    else:
        form = TechnicianForm(instance=technician, user_instance=technician.user)
        
    return render(request, 'core/technician_form.html', {
        'form': form,
        'title': 'Editar Técnico'
    })
# trigger
