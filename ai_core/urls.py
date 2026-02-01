from django.urls import path
from .views import processar_ia

urlpatterns = [
    path('processar/', processar_ia, name='processar_ia'),
]
