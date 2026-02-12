"""
URL configuration for erp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('comercial/', include('comercial.urls')),
    path('estoque/', include('estoque.urls')),
    path('operacional/', include('operacional.urls')),
    path('faturamento/', include('faturamento.urls')),
    path('relatorios/', include('reports.urls')),
    path('portal/', include('portal.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('ai/', include('ai_core.urls')),
    path('', include('integracao_cora.urls')),
    path('nfse-nacional/', include('nfse_nacional.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('importador/', include('importador.urls')),
]

# Serve media files (uploads) in all environments
# In production, consider using cloud storage (S3/GCS) for persistence
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    from django.urls import re_path
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
