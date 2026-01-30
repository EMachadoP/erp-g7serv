from django.urls import path
from . import views

app_name = 'operacional'
urlpatterns = [
    path('os/', views.service_order_list, name='service_order_list'),
    path('os/nova/', views.service_order_create, name='service_order_create'),
    path('os/<int:pk>/', views.service_order_detail, name='service_order_detail'),
    path('os/<int:pk>/editar/', views.service_order_update, name='service_order_update'),
    path('os/<int:pk>/cancelar/', views.service_order_cancel, name='service_order_cancel'),
    path('andamento/', views.operational_progress, name='operational_progress'),
    path('orcamentos/<int:pk>/liberar/', views.approve_budget, name='approve_budget'),
    path('orcamentos/<int:pk>/recusar/', views.refuse_budget, name='refuse_budget'),
    path('orcamentos/<int:pk>/gerar-os/', views.create_os_from_budget, name='create_os_from_budget'),
    path('os/<int:pk>/mobile/', views.service_order_mobile, name='service_order_mobile'),
    path('os/<int:pk>/mobile/finalizar/', views.service_order_finish_mobile, name='service_order_finish_mobile'),
    path('os/<int:pk>/pdf/', views.service_order_pdf, name='service_order_pdf'),
    # Mobile / Field Technician
    path('mobile/minhas-os/', views.mobile_os_list, name='mobile_os_list'),
    path('mobile/os/<int:pk>/', views.mobile_os_detail, name='mobile_os_detail'),
    path('api/os/<int:pk>/checkin/', views.api_checkin, name='api_checkin'),
    path('api/os/<int:pk>/upload/', views.api_upload_photo, name='api_upload_photo'),
    path('os/<int:pk>/mobile/checklist/', views.checklist_mobile_view, name='checklist_mobile'),
    path('api/os/<int:pk>/checklist/save/', views.save_checklist_api, name='save_checklist_api'),
    path('api/os/<int:pk>/checklist/finalize/', views.finalize_checklist_api, name='finalize_checklist_api'),
    path('os/<int:pk>/checklist/pdf/', views.service_order_checklist_pdf, name='service_order_checklist_pdf'),
    path('os/<int:pk>/checklist/email/', views.service_order_checklist_email, name='checklist_enviar_email'),
]
