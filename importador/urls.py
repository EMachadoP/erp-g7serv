from django.urls import path
from . import views

app_name = 'importador'

urlpatterns = [
    # UI Pages
    path('', views.IndexView.as_view(), name='index'),
    path('upload/', views.UploadPageView.as_view(), name='upload_page'),
    path('templates/', views.TemplatesPageView.as_view(), name='templates_page'),
    path('templates/<int:pk>/edit/', views.TemplateEditPageView.as_view(), name='template_edit'),
    path('importacoes/', views.ImportHistoryPageView.as_view(), name='history_page'),
    path('importacoes/<int:pk>/', views.ImportDetailPageView.as_view(), name='detail_page'),
    
    # API endpoints
    path('api/upload/', views.api_upload_file, name='api_upload'),
    path('api/modules/fields/<str:module_type>/', views.api_get_module_fields, name='api_fields'),
    path('api/templates/', views.TemplateListCreateAPI.as_view(), name='api_templates'),
    path('api/templates/<int:pk>/', views.TemplateDetailAPI.as_view(), name='api_template_detail'),
    path('api/import/', views.api_execute_import, name='api_import'),
    path('api/import/preview/', views.api_import_preview, name='api_preview'),
    path('api/import/jobs/', views.api_list_jobs, name='api_jobs'),
]
