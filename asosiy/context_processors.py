"""
Kontekst protsessorlari
"""
from .models import Kategoriya
from .views import savat_olish

def kategoriyalar(request):
    """Barcha sahifalarda kategoriyalarni ko'rsatish uchun kontekst protsessor"""
    return {
        'barcha_kategoriyalar': Kategoriya.objects.all()
    }

def savat_malumotlari(request):
    """Barcha sahifalarda savat ma'lumotlarini ko'rsatish uchun kontekst protsessor"""
    savat = savat_olish(request)
    savat_maxsulotlar_soni = sum(item.miqdor for item in savat.savatlar.all())
    return {
        'savat_maxsulotlar_soni': savat_maxsulotlar_soni
    }

