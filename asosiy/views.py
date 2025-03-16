"""
Asosiy ilova ko'rinishlari
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
import uuid

from .models import Kategoriya, Maxsulot, Savat, SavatMaxsulot, Buyurtma, BuyurtmaMaxsulot, OmborHarakati

def asosiy(request):
    """Asosiy sahifa ko'rinishi"""
    kategoriyalar = Kategoriya.objects.all()
    maxsulotlar = Maxsulot.objects.filter(mavjud=True)

    # Kategoriya bo'yicha filtrlash
    kategoriya_id = request.GET.get('kategoriya')
    if kategoriya_id:
        maxsulotlar = maxsulotlar.filter(kategoriya_id=kategoriya_id)

    # Qidiruv
    qidiruv = request.GET.get('qidiruv')
    if qidiruv:
        maxsulotlar = maxsulotlar.filter(
            Q(nomi__icontains=qidiruv) | Q(tavsif__icontains=qidiruv)
        )

    # Savatni olish
    savat = savat_olish(request)

    return render(request, 'asosiy/asosiy.html', {
        'kategoriyalar': kategoriyalar,
        'maxsulotlar': maxsulotlar,
    })

def maxsulot_tafsilotlari(request, maxsulot_id):
    """Maxsulot tafsilotlari sahifasi"""
    maxsulot = get_object_or_404(Maxsulot, id=maxsulot_id, mavjud=True)

    # O'xshash maxsulotlar
    oxshash_maxsulotlar = Maxsulot.objects.filter(
        kategoriya=maxsulot.kategoriya,
        mavjud=True
    ).exclude(id=maxsulot_id)[:4]

    return render(request, 'asosiy/maxsulot_tafsilotlari.html', {
        'maxsulot': maxsulot,
        'oxshash_maxsulotlar': oxshash_maxsulotlar,
    })

def savat_olish(request):
    """Foydalanuvchi savatini olish yoki yaratish"""
    if request.user.is_authenticated:
        # Ro'yxatdan o'tgan foydalanuvchi uchun
        savat, yaratilgan = Savat.objects.get_or_create(foydalanuvchi=request.user, defaults={'sessiya_id': None})
    else:
        # Ro'yxatdan o'tmagan foydalanuvchi uchun
        sessiya_id = request.session.get('savat_id')
        if not sessiya_id:
            # Yangi sessiya ID yaratish
            sessiya_id = str(uuid.uuid4())
            request.session['savat_id'] = sessiya_id

        savat, yaratilgan = Savat.objects.get_or_create(sessiya_id=sessiya_id, defaults={'foydalanuvchi': None})

    return savat

@csrf_exempt
@require_POST
def savatga_qoshish(request):
    """Maxsulotni savatga qo'shish"""
    data = json.loads(request.body)
    maxsulot_id = data.get('maxsulot_id')
    miqdor = int(data.get('miqdor', 1))

    # Maxsulotni tekshirish
    maxsulot = get_object_or_404(Maxsulot, id=maxsulot_id, mavjud=True)

    # Savatni olish
    savat = savat_olish(request)

    # Maxsulotni savatga qo'shish yoki yangilash
    savat_maxsulot, yaratilgan = SavatMaxsulot.objects.get_or_create(
        savat=savat,
        maxsulot=maxsulot,
        defaults={'miqdor': miqdor}
    )

    if not yaratilgan:
        # Agar maxsulot allaqachon savatda bo'lsa, miqdorini yangilash
        savat_maxsulot.miqdor += miqdor
        savat_maxsulot.save()

    # Savatdagi maxsulotlar sonini qaytarish
    savat_maxsulotlar_soni = sum(item.miqdor for item in savat.savatlar.all())

    return JsonResponse({
        'success': True,
        'savat_maxsulotlar_soni': savat_maxsulotlar_soni,
        'maxsulot_nomi': maxsulot.nomi
    })

def savat(request):
    """Savat sahifasi"""
    savat = savat_olish(request)
    savat_maxsulotlar = savat.savatlar.all()

    return render(request, 'asosiy/savat.html', {
        'savat': savat,
        'savat_maxsulotlar': savat_maxsulotlar,
    })

@csrf_exempt
@require_POST
def savat_yangilash(request):
    """Savatdagi maxsulot miqdorini yangilash"""
    data = json.loads(request.body)
    maxsulot_id = data.get('maxsulot_id')
    miqdor = int(data.get('miqdor', 1))

    # Savatni olish
    savat = savat_olish(request)

    try:
        savat_maxsulot = SavatMaxsulot.objects.get(savat=savat, maxsulot_id=maxsulot_id)

        if miqdor > 0:
            savat_maxsulot.miqdor = miqdor
            savat_maxsulot.save()
        else:
            savat_maxsulot.delete()

        # Yangilangan ma'lumotlarni qaytarish
        return JsonResponse({
            'success': True,
            'jami_narx': float(savat.jami_narx),
            'maxsulotlar_soni': savat.maxsulotlar_soni
        })
    except SavatMaxsulot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Maxsulot topilmadi'})

@csrf_exempt
@require_POST
def savat_tozalash(request):
    """Savatni to'liq tozalash"""
    savat = savat_olish(request)
    savat.savatlar.all().delete()

    return JsonResponse({'success': True})

def buyurtma_yaratish(request):
    """Buyurtma yaratish sahifasi"""
    savat = savat_olish(request)

    if savat.savatlar.count() == 0:
        messages.error(request, "Savatda maxsulotlar yo'q")
        return redirect('savat')

    # Foydalanuvchi tizimga kirmaganligini tekshirish
    if not request.user.is_authenticated:
        # Buyurtma yaratish sahifasiga o'tishdan oldin kirish sahifasiga yo'naltirish
        messages.info(request, "Buyurtma berish uchun avval tizimga kirishingiz kerak")
        return redirect(f"{reverse('kirish')}?next={reverse('buyurtma_yaratish')}")

    if request.method == 'POST':
        # Buyurtma ma'lumotlarini olish
        ism = request.POST.get('ism')
        familiya = request.POST.get('familiya')
        telefon = request.POST.get('telefon')
        manzil = request.POST.get('manzil')
        tolov_usuli = request.POST.get('tolov_usuli')

        # Buyurtma yaratish
        buyurtma = Buyurtma.objects.create(
            foydalanuvchi=request.user,
            ism=ism,
            familiya=familiya,
            telefon=telefon,
            manzil=manzil,
            tolov_usuli=tolov_usuli,
            jami_narx=savat.jami_narx
        )

        # Savatdagi maxsulotlarni buyurtmaga ko'chirish
        for savat_maxsulot in savat.savatlar.all():
            maxsulot = savat_maxsulot.maxsulot

            # Omborda yetarli miqdor borligini tekshirish
            if maxsulot.miqdor < savat_maxsulot.miqdor:
                messages.error(request, f"Kechirasiz, {maxsulot.nomi} maxsulotidan omborda faqat {maxsulot.miqdor} ta mavjud")
                buyurtma.delete()  # Buyurtmani bekor qilish
                return redirect('savat')

            # Buyurtma maxsulotini yaratish
            BuyurtmaMaxsulot.objects.create(
                buyurtma=buyurtma,
                maxsulot=maxsulot,
                miqdor=savat_maxsulot.miqdor,
                narx=maxsulot.chegirma_narx or maxsulot.narx,
                sotib_olish_narxi=maxsulot.sotib_olish_narxi
            )

            # Ombor harakatini yaratish
            OmborHarakati.objects.create(
                maxsulot=maxsulot,
                miqdor=savat_maxsulot.miqdor,
                harakat_turi='chiqim',
                izoh=f"Buyurtma #{buyurtma.id} orqali sotildi"
            )

        # Savatni tozalash
        savat.savatlar.all().delete()

        # Buyurtma tasdiqlandi xabarini ko'rsatish
        messages.success(request, "Buyurtmangiz muvaffaqiyatli qabul qilindi!")
        return redirect('buyurtma_tasdiqlandi', buyurtma_id=buyurtma.id)

    return render(request, 'asosiy/buyurtma_yaratish.html', {
        'savat': savat,
    })

def buyurtma_tasdiqlandi(request, buyurtma_id):
    """Buyurtma tasdiqlandi sahifasi"""
    buyurtma = get_object_or_404(Buyurtma, id=buyurtma_id)

    # Faqat o'z buyurtmasini ko'rish mumkin
    if request.user.is_authenticated and buyurtma.foydalanuvchi and buyurtma.foydalanuvchi != request.user and not request.user.is_staff:
        messages.error(request, "Siz bu buyurtmani ko'rish huquqiga ega emassiz")
        return redirect('asosiy')

    return render(request, 'asosiy/buyurtma_tasdiqlandi.html', {
        'buyurtma': buyurtma,
    })

@login_required
def buyurtmalarim(request):
    """Foydalanuvchi buyurtmalari sahifasi"""
    buyurtmalar = Buyurtma.objects.filter(foydalanuvchi=request.user).order_by('-yaratilgan_sana')

    return render(request, 'asosiy/buyurtmalarim.html', {
        'buyurtmalar': buyurtmalar,
    })

