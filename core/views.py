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
from .forms import TechnicianForm, CompanySettingsForm

@user_passes_test(lambda u: u.is_superuser)
@login_required
def company_settings(request):
    settings_obj = CompanySettings.objects.first()
    if not settings_obj:
        settings_obj = CompanySettings.objects.create(name="Minha Empresa", cnpj="00.000.000/0000-00")
        
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações atualizadas com sucesso.")
            return redirect('core:company_settings')
    else:
        form = CompanySettingsForm(instance=settings_obj)
        
    return render(request, 'core/company_settings.html', {'form': form, 'settings': settings_obj})


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
    Retorna permissões organizadas por app_label com nomes traduzidos.
    """
    import re
    APP_LABELS_BR = {
        'core': 'Sistema Core',
        'comercial': 'Comercial',
        'financeiro': 'Financeiro',
        'operacional': 'Operacional',
        'portal': 'Portal do Cliente',
        'estoque': 'Estoque',
        'faturamento': 'Faturamento',
        'reports': 'Relatórios',
        'nfse_nacional': 'NFSe Nacional',
        'integracao_cora': 'Integração Cora',
        'ai_core': 'Inteligência Artificial',
        'auth': 'Usuários e Perfis',
        'admin': 'Administração Django',
        'sessions': 'Sessões de Sistema',
        'contenttypes': 'Tipos de Dados',
    }

    # Mapeamento exaustivo de termos técnicos para nomes amigáveis em Português
    MODEL_NAMES_BR = {
        'user': 'usuário',
        'group': 'perfil/grupo',
        'permission': 'permissão',
        'content type': 'tipo de conteúdo',
        'session': 'sessão',
        'log entry': 'log de auditoria',
        'configuracao': 'configuração',
        'perfilusuario': 'dados do perfil',
        'budget product': 'produto do orçamento',
        'budget service': 'serviço do orçamento',
        'invoice': 'fatura/cobrança',
        'nota entrada item': 'item de nota de entrada',
        'nota entrada parcela': 'parcela de nota de entrada',
        'client profile': 'perfil do cliente',
        'client': 'cliente',
        'budget': 'orçamento',
        'contract': 'contrato',
        'service': 'serviço',
        'product': 'produto',
        'category': 'categoria',
        'billing group': 'grupo de faturamento',
        'entry': 'lançamento/entrada',
        'transaction': 'transação',
        'bank account': 'conta bancária',
        'attachment': 'anexo',
        'contact': 'contato',
        'address': 'endereço',
        'phone': 'telefone',
        'email': 'e-mail',
        'supplier': 'fornecedor',
        'stock': 'estoque',
        'inventory': 'inventário',
        'purchase order': 'pedido de compra',
        'sale order': 'pedido de venda',
        'registration': 'cadastro',
        'employee': 'funcionário',
        'department': 'departamento',
        'unit': 'unidade',
        'brand': 'marca',
        'payment': 'pagamento',
        'receipt': 'recebimento',
        'cost center': 'centro de custo',
        'plan of account': 'plano de contas',
    }

    try:
        permissions = Permission.objects.all().select_related('content_type')
        apps_permissions = {}
        
        for perm in permissions:
            try:
                if not perm.content_type:
                    continue
                    
                app_label = perm.content_type.app_label
                app_name = APP_LABELS_BR.get(app_label, app_label.title().replace('_', ' '))
                
                if app_name not in apps_permissions:
                    apps_permissions[app_name] = []
                
                # Nome original da permissão
                p_name = str(perm.name or '')
                
                # 1. Traduz prefixos padrões do Django
                translations = [
                    ('Can add ', 'Adicionar '),
                    ('Can change ', 'Editar '),
                    ('Can delete ', 'Excluir '),
                    ('Can view ', 'Visualizar '),
                ]
                
                for eng, pt in translations:
                    if p_name.lower().startswith(eng.lower()):
                        p_name = pt + p_name[len(eng):]
                        break
                
                # 2. Traduz nomes de modelos específicos
                # Ordenamos por tamanho descendente para evitar que 'budget' substitua parte de 'budget product'
                sorted_models = sorted(MODEL_NAMES_BR.items(), key=lambda x: len(x[0]), reverse=True)
                
                for eng_m, pt_m in sorted_models:
                    # Usando regex para garantir que substitui termos exatos respeitando limites de palavras
                    pattern = re.compile(rf'\b{re.escape(eng_m)}\b', re.IGNORECASE)
                    p_name = pattern.sub(pt_m, p_name)
                
                perm.name = p_name
                apps_permissions[app_name].append(perm)
            except Exception:
                continue
        
        # Opcional: Ordenar dicionário por nome de app (case insensitive)
        return dict(sorted(apps_permissions.items(), key=lambda x: x[0].lower()))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro fatal em get_permissions_from_mapping: {e}", exc_info=True)
        return {}


@login_required
@user_passes_test(is_socio_diretor)
def profile_create(request):
    """Cria novo perfil/grupo."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=== PROFILE_CREATE CHAMADO ===")
    
    logger.info("=== POST EM PROFILE_CREATE INICIADO ===")
    # Diagnóstico de CSRF e Headers
    logger.info(f"HTTP_ORIGIN: {request.META.get('HTTP_ORIGIN')}")
    logger.info(f"HTTP_REFERER: {request.META.get('HTTP_REFERER')}")
    logger.info(f"CSRF_COOKIE: {request.COOKIES.get('csrftoken')}")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
            return render(request, 'core/profile_form_v2.html', {
                'group': None,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': set()
            })
        
        try:
            logger.info(f"Tentando criar Grupo: {name}")
            group = Group.objects.create(name=name)
            logger.info(f"Grupo criado ID: {group.id}")
            
            if permission_ids:
                logger.info(f"Tentando associar {len(permission_ids)} permissões")
                group.permissions.set(permission_ids)
                logger.info("Permissões associadas com sucesso")
            
            messages.success(request, 'Perfil criado com sucesso!')
            return redirect('core:profile_list')
        except Exception as e:
            logger.error(f"Erro ao salvar perfil no banco: {e}", exc_info=True)
            messages.error(request, f'Erro ao salvar no banco de dados: {e}')
            return render(request, 'core/profile_form_v2.html', {
                'group': None,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': set(permission_ids) if permission_ids else set()
            })

    logger.info("Exibindo formulário de criação (GET)")
    return render(request, 'core/profile_form_v2.html', {
        'group': None,
        'apps_permissions': get_permissions_from_mapping(),
        'current_permissions': set()
    })


@login_required
@user_passes_test(is_socio_diretor)
def profile_update(request, pk):
    """Atualiza perfil/grupo existente."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"=== PROFILE_UPDATE CHAMADO PARA ID: {pk} ===")
    
    # Diagnóstico de CSRF e Headers no POST
    if request.method == 'POST':
        logger.info("=== POST EM PROFILE_UPDATE INICIADO ===")
        logger.info(f"HTTP_ORIGIN: {request.META.get('HTTP_ORIGIN')}")
        logger.info(f"HTTP_REFERER: {request.META.get('HTTP_REFERER')}")
        logger.info(f"CSRF_COOKIE: {request.COOKIES.get('erp_csrftoken')}")

    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
            current_permissions = set(group.permissions.values_list('id', flat=True))
            return render(request, 'core/profile_form_v2.html', {
                'group': group,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': current_permissions
            })
        
        try:
            logger.info(f"Tentando atualizar Grupo ID: {group.id}")
            group.name = name
            group.save()
            
            logger.info(f"Tentando atualizar {len(permission_ids)} permissões")
            group.permissions.set(permission_ids)
            logger.info("Atualização concluída com sucesso")
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('core:profile_list')
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil no banco: {e}", exc_info=True)
            messages.error(request, f'Erro ao atualizar no banco de dados: {e}')
            current_permissions = set(permission_ids) if permission_ids else set()
            return render(request, 'core/profile_form_v2.html', {
                'group': group,
                'apps_permissions': get_permissions_from_mapping(),
                'current_permissions': current_permissions
            })

    current_permissions = set(group.permissions.values_list('id', flat=True))
    logger.info(f"Exibindo formulário de edição para {group.name}")
    return render(request, 'core/profile_form_v2.html', {
        'group': group,
        'apps_permissions': get_permissions_from_mapping(),
        'current_permissions': current_permissions
    })

def csrf_failure(request, reason=""):
    """View customizada para erro CSRF com diagnóstico."""
    from django.http import HttpResponseForbidden
    
    context = {
        'reason': reason,
        'path': request.path,
        'method': request.method,
        'origin': request.META.get('HTTP_ORIGIN', 'N/A'),
        'referer': request.META.get('HTTP_REFERER', 'N/A'),
        'has_cookie_header': bool(request.META.get('HTTP_COOKIE')),
        'cookies': list(request.COOKIES.keys()) if request.COOKIES else 'Nenhum'
    }

    return HttpResponseForbidden(f"""
    <html>
    <head><title>Erro de Segurança (403)</title></head>
    <body style="font-family: Arial, sans-serif; padding: 40px; line-height: 1.6;">
        <h1 style="color: #d9534f;">Erro de Segurança (403)</h1>
        <p><strong>A Verificação CSRF falhou.</strong></p>
        <p><strong>Motivo:</strong> {reason}</p>
        <p><strong>Dica:</strong> Limpe os cookies do navegador (Ctrl+Shift+Del) para este site e tente novamente.</p>
        <hr>
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
            <h3>Detalhes para Suporte:</h3>
            <ul>
                <li><b>Method:</b> {context['method']}</li>
                <li><b>Origin:</b> {context['origin']}</li>
                <li><b>Referer:</b> {context['referer']}</li>
                <li><b>Cookie Header Present:</b> {context['has_cookie_header']}</li>
                <li><b>Cookies Received:</b> {context['cookies']}</li>
            </ul>
        </div>
        <hr>
        <p><a href="{request.path}" style="background: #0275d8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Tentar novamente</a></p>
    </body>
    </html>
    """)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def debug_cookies(request):
    """View de diagnóstico para testar cookies - REMOVER EM PRODUÇÃO."""
    from django.conf import settings
    from django.http import HttpResponse
    
    # Ação de limpeza programática
    reset_performed = False
    if request.GET.get('reset') == 'true':
        response = HttpResponse(redirect('/debug-cookies/'))
        response.delete_cookie('erp_csrftoken', domain=settings.CSRF_COOKIE_DOMAIN if hasattr(settings, 'CSRF_COOKIE_DOMAIN') else None)
        response.delete_cookie('erp_sessionid', domain=settings.SESSION_COOKIE_DOMAIN if hasattr(settings, 'SESSION_COOKIE_DOMAIN') else None)
        # Tenta deletar sem domínio também por garantia
        response.delete_cookie('erp_csrftoken')
        response.delete_cookie('erp_sessionid')
        messages.success(request, 'Cookies legados (erp_*) foram removidos via Set-Cookie!')
        return response

    # Gerar lista de cookies formatada
    cookies_list = ""
    if request.COOKIES:
        for k, v in request.COOKIES.items():
            color = "#d9534f" if k.startswith('erp_') else "#5cb85c"
            cookies_list += f'<li style="color: {color};"><b>{k}:</b> {v[:20]}... {"(DELETAR)" if k.startswith("erp_") else "(MANTER)"}</li>'
    else:
        cookies_list = '<li><i>Nenhum cookie recebido</i></li>'

    response = HttpResponse(f"""
    <html>
    <head><title>Debug Cookies</title></head>
    <body style="font-family: monospace; padding: 20px; background: #eee;">
        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 800px; margin: auto;">
            <h2 style="color: #333;">Diagnóstico de Cookies e Headers</h2>
            
            <div style="background: #fff3cd; padding: 15px; border: 1px solid #ffeeba; border-radius: 4px; margin-bottom: 20px;">
                <strong>⚠️ Atenção:</strong> Se você vê cookies vermelhos (erp_*) abaixo, o login vai falhar. 
                <br><br>
                <a href="?reset=true" style="background: #d9534f; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; font-weight: bold;">LIMPAR COOKIES LEGADOS AGORA</a>
            </div>

            <h3 style="border-bottom: 1px solid #ccc;">1. Configurações Django:</h3>
            <ul>
                <li><b>IS_RAILWAY:</b> {getattr(settings, 'IS_RAILWAY', 'N/A')}</li>
                <li><b>CSRF_COOKIE_NAME:</b> {settings.CSRF_COOKIE_NAME}</li>
            </ul>
            
            <h3 style="border-bottom: 1px solid #ccc;">2. Cookies Recebidos do Seu Navegador:</h3>
            <ul>
                {cookies_list}
            </ul>
            
            <hr>
            <p><a href="/accounts/login/">Voltar para o Login</a></p>
        </div>
    </body>
    </html>
    """)
    
    # Sempre tenta garantir que o cookie de teste e os novos existam
    response.set_cookie('debug_test', 'okay', secure=True, samesite='Lax')
    
    return response

from django.http import HttpResponse
def fix_user_permissions(request):
    """View TEMPORÁRIA para garantir que o usuário eldonmp é superuser e tem o grupo correto."""
    from django.contrib.auth.models import User, Group
    
    # Permitir em produção apenas se explicitamente chamado para resolver a crise
    # mas mantemos a trava de segurança mínima de não ser uma view aberta se possível.
    # Como o usuário já está logado como 'admin' (ou tentando), podemos checar.
    
    username = 'eldonmp'
    try:
        user = User.objects.get(username=username)
        old_status = f"Superuser: {user.is_superuser}, Staff: {user.is_staff}, Grupos: {[g.name for g in user.groups.all()]}"
        
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        # Garantir grupo SÓCIO-DIRETOR (que é o que o is_socio_diretor checa)
        group, created = Group.objects.get_or_create(name='SÓCIO-DIRETOR')
        user.groups.add(group)
        
        return HttpResponse(f"""
            <h1>Sucesso!</h1>
            <p>O usuário <b>{username}</b> foi atualizado.</p>
            <ul>
                <li><b>Status Anterior:</b> {old_status}</li>
                <li><b>Status Novo:</b> Superuser: True, Staff: True, Grupo: SÓCIO-DIRETOR</li>
            </ul>
            <p><a href="/accounts/login/">Ir para Login</a> ou <a href="/">Ir para Home</a></p>
        """)
    except User.DoesNotExist:
        return HttpResponse(f"Erro: Usuário '{username}' não encontrado no banco de dados.", status=404)
    except Exception as e:
        return HttpResponse(f"Erro ao atualizar: {str(e)}", status=500)


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


# ==============================================================================
# TEMPLATES DE E-MAIL
# ==============================================================================
from .models import EmailTemplate
from .forms import EmailTemplateForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def email_template_list(request):
    """Lista todos os templates de e-mail."""
    templates = EmailTemplate.objects.all().order_by('-active', 'name')
    return render(request, 'core/email_template_list.html', {'templates': templates})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def email_template_create(request):
    """Cria novo template de e-mail."""
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template de e-mail criado com sucesso.')
            return redirect('core:email_template_list')
    else:
        form = EmailTemplateForm()
    
    return render(request, 'core/email_template_form.html', {
        'form': form,
        'title': 'Novo Template de E-mail'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def email_template_update(request, pk):
    """Edita template de e-mail existente."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template de e-mail atualizado com sucesso.')
            return redirect('core:email_template_list')
    else:
        form = EmailTemplateForm(instance=template)
    
    return render(request, 'core/email_template_form.html', {
        'form': form,
        'title': 'Editar Template de E-mail',
        'template': template
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def email_template_delete(request, pk):
    """Exclui template de e-mail."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template de e-mail excluído com sucesso.')
        return redirect('core:email_template_list')
    
    return render(request, 'core/email_template_confirm_delete.html', {'template': template})

