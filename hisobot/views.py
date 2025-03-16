"""
Hisobot ilova ko'rinishlari
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F, DecimalField, Count
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from asosiy.models import Maxsulot, Buyurtma, BuyurtmaMaxsulot, OmborHarakati

def is_staff(user):
    """Foydalanuvchi admin yoki xodim ekanligini tekshirish"""
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def hisobotlar(request):
    """Hisobotlar sahifasi"""
    # Vaqt oralig'ini olish
    vaqt_oralig = request.GET.get('vaqt_oralig', 'bugun')

    # Vaqt oralig'iga qarab sana chegaralarini aniqlash
    bugun = timezone.now().date()

    if vaqt_oralig == 'bugun':
        boshlanish_sana = bugun
        tugash_sana = bugun + timedelta(days=1)
        title = "Bugungi hisobot"
    elif vaqt_oralig == 'hafta':
        boshlanish_sana = bugun - timedelta(days=bugun.weekday())
        tugash_sana = boshlanish_sana + timedelta(days=7)
        title = "Haftalik hisobot"
    elif vaqt_oralig == 'oy':
        boshlanish_sana = bugun.replace(day=1)
        if bugun.month == 12:
            tugash_sana = bugun.replace(year=bugun.year + 1, month=1, day=1)
        else:
            tugash_sana = bugun.replace(month=bugun.month + 1, day=1)
        title = "Oylik hisobot"
    elif vaqt_oralig == 'yil':
        boshlanish_sana = bugun.replace(month=1, day=1)
        tugash_sana = bugun.replace(year=bugun.year + 1, month=1, day=1)
        title = "Yillik hisobot"
    else:
        # Agar noto'g'ri vaqt oralig'i berilgan bo'lsa, bugungi kunni olish
        boshlanish_sana = bugun
        tugash_sana = bugun + timedelta(days=1)
        title = "Bugungi hisobot"

    # Timezone-aware datetime objects yaratish
    boshlanish_sana = timezone.make_aware(timezone.datetime.combine(boshlanish_sana, timezone.datetime.min.time()))
    tugash_sana = timezone.make_aware(timezone.datetime.combine(tugash_sana, timezone.datetime.min.time()))

    # Buyurtmalar bo'yicha hisobotlar
    buyurtmalar = Buyurtma.objects.filter(
        yaratilgan_sana__gte=boshlanish_sana,
        yaratilgan_sana__lt=tugash_sana
    )

    # Umumiy savdo hajmi
    jami_savdo = buyurtmalar.aggregate(
        jami=Coalesce(Sum('jami_narx'), 0, output_field=DecimalField())
    )['jami']

    # Umumiy foyda
    jami_foyda = 0
    for buyurtma in buyurtmalar:
        jami_foyda += buyurtma.jami_foyda

    # Buyurtmalar soni
    buyurtmalar_soni = buyurtmalar.count()

    # Eng ko'p sotilgan maxsulotlar
    eng_kop_sotilgan = BuyurtmaMaxsulot.objects.filter(
        buyurtma__yaratilgan_sana__gte=boshlanish_sana,
        buyurtma__yaratilgan_sana__lt=tugash_sana
    ).values('maxsulot__nomi').annotate(
        jami_miqdor=Sum('miqdor')
    ).order_by('-jami_miqdor')[:10]

    # Eng ko'p foyda keltirgan maxsulotlar
    eng_kop_foyda = BuyurtmaMaxsulot.objects.filter(
        buyurtma__yaratilgan_sana__gte=boshlanish_sana,
        buyurtma__yaratilgan_sana__lt=tugash_sana
    ).values('maxsulot__nomi').annotate(
        jami_foyda=Sum(F('narx') - F('sotib_olish_narxi'), output_field=DecimalField()) * Sum('miqdor')
    ).order_by('-jami_foyda')[:10]

    # Ombordagi maxsulotlar
    ombordagi_maxsulotlar = Maxsulot.objects.filter(mavjud=True, miqdor__gt=0)

    # Ombordagi jami maxsulotlar qiymati
    ombor_qiymati = ombordagi_maxsulotlar.aggregate(
        jami=Coalesce(Sum(F('sotib_olish_narxi') * F('miqdor')), 0, output_field=DecimalField())
    )['jami']

    # Ombordagi maxsulotlar soni
    ombor_maxsulotlar_soni = ombordagi_maxsulotlar.count()

    # Ombordagi jami maxsulotlar miqdori
    ombor_jami_miqdor = ombordagi_maxsulotlar.aggregate(
        jami=Coalesce(Sum('miqdor'), 0)
    )['jami']

    # Yo'qotilgan va muddati o'tgan maxsulotlar
    yoqotilgan_maxsulotlar = OmborHarakati.objects.filter(
        harakat_turi__in=['yo_qotish', 'muddati_otgan'],
        sana__gte=boshlanish_sana,
        sana__lt=tugash_sana
    )

    # Yo'qotilgan va muddati o'tgan maxsulotlar qiymati
    yoqotilgan_qiymat = 0
    for harakat in yoqotilgan_maxsulotlar:
        yoqotilgan_qiymat += harakat.maxsulot.sotib_olish_narxi * harakat.miqdor

    # Kunlik savdo dinamikasi (faqat oy va yil uchun)
    kunlik_savdo = []
    if vaqt_oralig in ['oy', 'yil']:
        kunlik_savdo = Buyurtma.objects.filter(
            yaratilgan_sana__gte=boshlanish_sana,
            yaratilgan_sana__lt=tugash_sana
        ).annotate(
            kun=TruncDay('yaratilgan_sana')
        ).values('kun').annotate(
            jami=Sum('jami_narx')
        ).order_by('kun')

    # Oylik savdo dinamikasi (faqat yil uchun)
    oylik_savdo = []
    if vaqt_oralig == 'yil':
        oylik_savdo = Buyurtma.objects.filter(
            yaratilgan_sana__gte=boshlanish_sana,
            yaratilgan_sana__lt=tugash_sana
        ).annotate(
            oy=TruncMonth('yaratilgan_sana')
        ).values('oy').annotate(
            jami=Sum('jami_narx')
        ).order_by('oy')

    # Yangi shablon nomini ishlatish
    return render(request, 'hisobot/hisobotlar_new.html', {
        'title': title,
        'vaqt_oralig': vaqt_oralig,
        'jami_savdo': jami_savdo,
        'jami_foyda': jami_foyda,
        'buyurtmalar_soni': buyurtmalar_soni,
        'eng_kop_sotilgan': eng_kop_sotilgan,
        'eng_kop_foyda': eng_kop_foyda,
        'ombor_qiymati': ombor_qiymati,
        'ombor_maxsulotlar_soni': ombor_maxsulotlar_soni,
        'ombor_jami_miqdor': ombor_jami_miqdor,
        'yoqotilgan_qiymat': yoqotilgan_qiymat,
        'kunlik_savdo': kunlik_savdo,
        'oylik_savdo': oylik_savdo,
    })

@login_required
@user_passes_test(is_staff)
def barcode_skaner(request):
    """Barcode skaner sahifasi"""
    maxsulot = None
    xabar = None

    if request.method == 'POST':
        barcode = request.POST.get('barcode')

        if barcode:
            try:
                maxsulot = Maxsulot.objects.get(barcode=barcode)
            except Maxsulot.DoesNotExist:
                xabar = f"Barcode {barcode} bilan maxsulot topilmadi"

    return render(request, 'hisobot/barcode_skaner.html', {
        'maxsulot': maxsulot,
        'xabar': xabar,
    })

@login_required
@user_passes_test(is_staff)
def maxsulot_sotish(request):
    """Maxsulot sotish sahifasi"""
    maxsulot = None
    xabar = None

    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        miqdor = request.POST.get('miqdor', 1)

        try:
            miqdor = int(miqdor)
            if miqdor <= 0:
                xabar = "Miqdor 0 dan katta bo'lishi kerak"
                return render(request, 'hisobot/maxsulot_sotish.html', {
                    'maxsulot': maxsulot,
                    'xabar': xabar,
                })
        except ValueError:
            xabar = "Miqdor son bo'lishi kerak"
            return render(request, 'hisobot/maxsulot_sotish.html', {
                'maxsulot': maxsulot,
                'xabar': xabar,
            })

        if barcode:
            try:
                maxsulot = Maxsulot.objects.get(barcode=barcode)

                # Maxsulot mavjudligini tekshirish
                if not maxsulot.mavjud:
                    xabar = f"{maxsulot.nomi} maxsuloti mavjud emas"
                    return render(request, 'hisobot/maxsulot_sotish.html', {
                        'maxsulot': maxsulot,
                        'xabar': xabar,
                    })

                # Omborda yetarli miqdor borligini tekshirish
                if maxsulot.miqdor < miqdor:
                    xabar = f"Omborda faqat {maxsulot.miqdor} ta {maxsulot.nomi} mavjud"
                    return render(request, 'hisobot/maxsulot_sotish.html', {
                        'maxsulot': maxsulot,
                        'xabar': xabar,
                    })

                # Maxsulotni sotish
                narx = maxsulot.chegirma_narx if maxsulot.chegirma_narx else maxsulot.narx

                # Buyurtma yaratish
                buyurtma = Buyurtma.objects.create(
                    foydalanuvchi=request.user,
                    ism="Kassa orqali sotildi",
                    familiya="",
                    telefon="",
                    manzil="",
                    tolov_usuli='naqd',
                    holat='yetkazilgan',
                    jami_narx=narx * miqdor
                )

                # Buyurtma maxsulotini yaratish
                BuyurtmaMaxsulot.objects.create(
                    buyurtma=buyurtma,
                    maxsulot=maxsulot,
                    miqdor=miqdor,
                    narx=narx,
                    sotib_olish_narxi=maxsulot.sotib_olish_narxi
                )

                # Ombor harakatini yaratish
                OmborHarakati.objects.create(
                    maxsulot=maxsulot,
                    miqdor=miqdor,
                    harakat_turi='chiqim',
                    izoh=f"Kassa orqali sotildi. Buyurtma #{buyurtma.id}"
                )

                xabar = f"{miqdor} ta {maxsulot.nomi} muvaffaqiyatli sotildi"
                maxsulot = None  # Yangi maxsulot uchun formani tozalash

            except Maxsulot.DoesNotExist:
                xabar = f"Barcode {barcode} bilan maxsulot topilmadi"

    return render(request, 'hisobot/maxsulot_sotish.html', {
        'maxsulot': maxsulot,
        'xabar': xabar,
    })

@login_required
@user_passes_test(is_staff)
def ombor_boshqarish(request):
    """Ombor boshqarish sahifasi"""
    maxsulot = None
    xabar = None

    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        miqdor = request.POST.get('miqdor', 1)
        harakat_turi = request.POST.get('harakat_turi', 'kirim')
        izoh = request.POST.get('izoh', '')

        try:
            miqdor = int(miqdor)
            if miqdor <= 0:
                xabar = "Miqdor 0 dan katta bo'lishi kerak"
                return render(request, 'hisobot/ombor_boshqarish.html', {
                    'maxsulot': maxsulot,
                    'xabar': xabar,
                })
        except ValueError:
            xabar = "Miqdor son bo'lishi kerak"
            return render(request, 'hisobot/ombor_boshqarish.html', {
                'maxsulot': maxsulot,
                'xabar': xabar,
            })

        if barcode:
            try:
                maxsulot = Maxsulot.objects.get(barcode=barcode)

                # Chiqim, yo'qotish yoki muddati o'tgan bo'lsa, omborda yetarli miqdor borligini tekshirish
                if harakat_turi in ['chiqim', 'yo_qotish', 'muddati_otgan']:
                    if maxsulot.miqdor < miqdor:
                        xabar = f"Omborda faqat {maxsulot.miqdor} ta {maxsulot.nomi} mavjud"
                        return render(request, 'hisobot/ombor_boshqarish.html', {
                            'maxsulot': maxsulot,
                            'xabar': xabar,
                        })

                # Ombor harakatini yaratish
                OmborHarakati.objects.create(
                    maxsulot=maxsulot,
                    miqdor=miqdor,
                    harakat_turi=harakat_turi,
                    izoh=izoh
                )

                xabar = f"{miqdor} ta {maxsulot.nomi} uchun {harakat_turi} harakati muvaffaqiyatli yaratildi"
                maxsulot = None  # Yangi maxsulot uchun formani tozalash

            except Maxsulot.DoesNotExist:
                xabar = f"Barcode {barcode} bilan maxsulot topilmadi"
            except ValueError as e:
                xabar = str(e)

    return render(request, 'hisobot/ombor_boshqarish.html', {
        'maxsulot': maxsulot,
        'xabar': xabar,
    })

