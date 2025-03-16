"""
Utility funksiyalar
"""
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied


def custom_exception_handler(exc, context):
    """Custom exception handler for REST framework"""
    response = exception_handler(exc, context)

    # Agar foydalanuvchi autentifikatsiyadan o'tmagan bo'lsa
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated, PermissionDenied)):
        request = context.get('request')
        if request and not request.accepted_renderer.format == 'json':
            # API so'rovlari uchun emas, oddiy sahifa so'rovlari uchun
            messages.error(request, "Bu sahifani ko'rish uchun avval tizimga kirishingiz kerak")
            return HttpResponseRedirect(f"{reverse('kirish')}?next={request.path}")

    return response

