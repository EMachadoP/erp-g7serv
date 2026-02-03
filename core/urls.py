from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('fix-user/', views.fix_user_permissions, name='fix_user_permissions'),
    path('', views.home, name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Users
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
    path('usuarios/<int:pk>/alterar-senha/', views.user_change_password, name='user_change_password'),
    path('usuarios/<int:pk>/alternar-status/', views.user_toggle_active, name='user_toggle_active'),
    path('usuarios/<int:pk>/remover/', views.user_delete, name='user_delete'),
    
    # Profiles
    path('perfis/', views.profile_list, name='profile_list'),
    path('perfis/novo/', views.profile_create, name='profile_create'),
    path('perfis/<int:pk>/editar/', views.profile_update, name='profile_update'),
    
    # Technician URLs
    path('tecnicos/', views.technician_list, name='technician_list'),
    path('tecnicos/novo/', views.technician_create, name='technician_create'),
    path('tecnicos/<int:pk>/editar/', views.technician_update, name='technician_update'),
    
    # System Settings
    path('configuracoes/', views.company_settings, name='company_settings'),
]
