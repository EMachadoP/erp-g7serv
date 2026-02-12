from django.urls import path
from . import views

app_name = 'estoque'
urlpatterns = [
    path('produtos/', views.product_list, name='product_list'),
    path('produtos/novo/', views.product_create, name='product_create'),
    path('produtos/<int:pk>/', views.product_detail, name='product_detail'),
    path('produtos/<int:pk>/editar/', views.product_update, name='product_update'),
    path('movimentacoes/', views.movement_list, name='movement_list'),
    path('movimentacoes/nova/', views.movement_create, name='movement_create'),
    
    # Marcas
    path('marcas/', views.brand_list, name='brand_list'),
    path('marcas/nova/', views.brand_create, name='brand_create'),
    path('marcas/<int:pk>/editar/', views.brand_update, name='brand_update'),
    
    # Categorias
    path('categorias/', views.category_list, name='category_list'),
    path('categorias/nova/', views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', views.category_update, name='category_update'),

    # Locais
    path('locais/', views.location_list, name='location_list'),
    path('locais/nova/', views.location_create, name='location_create'),
    path('locais/<int:pk>/editar/', views.location_update, name='location_update'),

    # Famílias
    path('familias/nova/', views.family_create, name='family_create'),
    path('familias/<int:pk>/editar/', views.family_update, name='family_update'),

    # Cadastros Auxiliares (tela unificada)
    path('cadastros/', views.cadastros_auxiliares, name='cadastros_auxiliares'),

    # HTMX Partials
    path('htmx/familia/nova/', views.htmx_family_create, name='htmx_family_create'),
    path('htmx/local/novo/', views.htmx_location_create, name='htmx_location_create'),

    # Balanços (Inventário)
    path('balancos/', views.inventory_list, name='inventory_list'),
    path('balancos/novo/', views.inventory_create, name='inventory_create'),
    path('balancos/<int:pk>/', views.inventory_detail, name='inventory_detail'),
]
