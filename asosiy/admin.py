"""
Admin panel konfiguratsiyasi
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import Kategoriya, Maxsulot, Savat, SavatMaxsulot, Buyurtma, BuyurtmaMaxsulot, OmborHarakati


@admin.register(Kategoriya)
class KategoriyaAdmin(admin.ModelAdmin):
    """Kategoriya admin konfiguratsiyasi"""
    list_display = ('nomi', 'yaratilgan_sana')
    search_fields = ('nomi',)


class SavatMaxsulotInline(admin.TabularInline):
    """Savat maxsulotlarini ko'rsatish uchun inline"""
    model = SavatMaxsulot
    extra = 0


@admin.register(Savat)
class SavatAdmin(admin.ModelAdmin):
    """Savat admin konfiguratsiyasi"""
    list_display = ('id', 'foydalanuvchi', 'yaratilgan_sana', 'jami_narx', 'maxsulotlar_soni')
    inlines = [SavatMaxsulotInline]


class OmborHarakatiInline(admin.TabularInline):
    """Ombor harakatlarini ko'rsatish uchun inline"""
    model = OmborHarakati
    extra = 0
    readonly_fields = ('sana',)


@admin.register(Maxsulot)
class MaxsulotAdmin(admin.ModelAdmin):
    """Maxsulot admin konfiguratsiyasi"""
    list_display = (
    'nomi', 'kategoriya', 'narx', 'sotib_olish_narxi', 'foyda_display', 'chegirma_narx', 'mavjud', 'miqdor',
    'yaratilgan_sana')
    list_filter = ('kategoriya', 'mavjud')
    search_fields = ('nomi', 'tavsif', 'barcode')
    readonly_fields = ('foyda_display',)
    inlines = [OmborHarakatiInline]

    def foyda_display(self, obj):
        """Foydani ko'rsatish"""
        if obj.foyda > 0:
            return format_html('<span style="color:green">+{}</span>', obj.foyda)
        return format_html('<span style="color:red">{}</span>', obj.foyda)

    foyda_display.short_description = 'Foyda'


class BuyurtmaMaxsulotInline(admin.TabularInline):
    """Buyurtma maxsulotlarini ko'rsatish uchun inline"""
    model = BuyurtmaMaxsulot
    extra = 0
    readonly_fields = ('maxsulot', 'miqdor', 'narx', 'sotib_olish_narxi', 'foyda')


@admin.register(Buyurtma)
class BuyurtmaAdmin(admin.ModelAdmin):
    """Buyurtma admin konfiguratsiyasi"""
    list_display = (
    'id', 'ism', 'familiya', 'telefon', 'holat', 'tolov_usuli', 'jami_narx', 'jami_foyda', 'yaratilgan_sana')
    list_filter = ('holat', 'tolov_usuli', 'yaratilgan_sana')
    search_fields = ('ism', 'familiya', 'telefon')
    readonly_fields = ('jami_narx', 'jami_foyda')
    inlines = [BuyurtmaMaxsulotInline]

    def get_readonly_fields(self, request, obj=None):
        """Tahrirlash mumkin bo'lmagan maydonlarni belgilash"""
        if obj:  # Agar buyurtma mavjud bo'lsa
            return self.readonly_fields + ('foydalanuvchi', 'ism', 'familiya', 'telefon', 'manzil', 'tolov_usuli')
        return self.readonly_fields


@admin.register(OmborHarakati)
class OmborHarakatiAdmin(admin.ModelAdmin):
    """Ombor harakati admin konfiguratsiyasi"""
    list_display = ('maxsulot', 'miqdor', 'harakat_turi', 'sana')
    list_filter = ('harakat_turi', 'sana')
    search_fields = ('maxsulot__nomi', 'izoh')
    date_hierarchy = 'sana'


## 6. Hisobot ilovasini yaratish

# ```tsx
# file = "hisobot/models.py"
# """
# Hisobot ilova modellari
# """
from django.db import models

# Hisobot ilovasi uchun modellar kerak emas, chunki biz mavjud modellardan foydalanib hisobotlarni yaratamiz

