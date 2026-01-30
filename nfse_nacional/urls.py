from django.urls import path
from . import views

app_name = 'nfse_nacional'

urlpatterns = [
    # Empresa URLs
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/nova/', views.empresa_create, name='empresa_create'),
    path('empresas/<int:pk>/editar/', views.empresa_update, name='empresa_update'),

    # NFSe URLs
    path('nfse/', views.nfse_list, name='nfse_list'),
    path('nfse/nova/', views.nfse_create, name='nfse_create'),
]
