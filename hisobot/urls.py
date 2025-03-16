"""
Hisobot ilova URL konfiguratsiyasi
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.hisobotlar, name='hisobotlar'),
    path('barcode-skaner/', views.barcode_skaner, name='barcode_skaner'),
    path('maxsulot-sotish/', views.maxsulot_sotish, name='maxsulot_sotish'),
    path('ombor-boshqarish/', views.ombor_boshqarish, name='ombor_boshqarish'),
]

