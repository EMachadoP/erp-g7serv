from django.urls import path
from . import views

app_name = 'portal'
urlpatterns = [
    path('', views.portal_home, name='home'),
    path('faturas/', views.portal_invoice_list, name='invoice_list'),
    path('os/', views.portal_os_list, name='os_list'),
]
