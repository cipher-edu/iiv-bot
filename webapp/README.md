# IIV EduBot Web App (v2.0)

Telegram Mini App (Web App) va to'liq formatli Admin Dashboard platformasi.

## Texnologik stek
- **Freymvork:** Next.js 14+ (App Router, TypeScript)
- **Stillar:** Tailwind CSS, Lucide Icons
- **Telegram SDK:** Telegram WebApp SDK (`telegram-web-app.js`)
- **Autentifikatsiya:** Telegram `initData` (HMAC-SHA256) va Admin sessiyalari

---

## Panellar va Tuzilishi

### 1. Foydalanuvchi paneli (Telegram Mini App) — `app/(user)/`
Mobil qurilmalar va Telegram ilovasi ichida to'liq ekranli ochilishga moslashtirilgan:
- **Asosiy sahifa (`/`)**: Foydalanuvchi ma'lumotlari, kunlik streak, davom ettirishdagi kurs, tezkor test.
- **Kurslar katalogi (`/courses`)**: Sohaviy toifalar, qidiruv va kurs kartochkalari.
- **Darslar pleyeri (`/courses/[id]`)**: Video darslar, matnli o'quv materiallari, yuklab olinuvchi PDF ilovalar, 1-5 yulduzli baholash modali.
- **Testlar katalogi (`/tests`)**: Kurs va attestatsiya testlari ro'yxati, oldingi natijalar.
- **Interaktiv test topshirish (`/tests/[id]`)**: Jonli teskari hisoblovchi taymer, savollar matritsasi, javoblarni belgilash va natijalar ekrani.
- **Reyting & Gamifikatsiya (`/rating`)**: Haftalik peshqadamlar shohsupasi (1, 2, 3-o'rinlar), to'plangan ballar, ochilgan nishonlar (badges).
- **AI Tyutor (`/ai-tutor`)**: Claude / GPT yordamida o'quvchi savollariga javob beruvchi sun'iy intellektli chat yordamchisi.
- **Shaxsiy profil (`/profile`)**: Xodim ma'lumotlari, darajasi, haqiqiy QR-kodli rasmiy PDF sertifikatlar modali.

### 2. Administrator paneli (Desktop Dashboard) — `app/(admin)/admin/`
Kompyuter brauzerida to'liq formatda boshqarish uchun mo'ljallangan:
- **Analitika va Boshqaruv (`/admin`)**: Jami foydalanuvchilar, bugungi faollik, drop-off tahlili, so'nggi ro'yxatdan o'tganlar.
- **Kurslar konstruktori (`/admin/courses`)**: Barcha kurslar jadvali, tahrirlash, o'chirish.
- **Yangi kurs yaratish (`/admin/courses/new`)**: Kurs ma'lumotlari, modullar va darslar qo'shish konstruktori.
- **Testlar va AI Generator (`/admin/tests`)**: Dars matnidan AI orqali avtomatik test savollari va variantlarini shakllantirish vositasi.
- **Foydalanuvchilar & Rollar (`/admin/users`)**: Xodimlar va fuqarolar ro'yxati, rollarni o'zgartirish (Fuqaro, Xodim, Moderator, Admin), muddatli bloklash (1 soat, 1 kun, 7 kun, 30 kun, muddatsiz).
- **Ommaviy xabarnoma (`/admin/broadcast`)**: Telegram foydalanuvchilariga segmentlar bo'yicha (Barchaga, Xodimlarga, Faollarga) jonli Telegram ko'rinishiga ega xabar yuborish.
- **Xavfsizlik va Audit (`/admin/audit`)**: PostgreSQL, Redis, MinIO serverlari holati va barcha admin harakatlari logi.

---

## Lokal kompyuterda ishga tushirish

```bash
cd webapp
npm run dev
```

Brauzerda:
- Foydalanuvchi Mini App: `http://localhost:3000`
- Administrator Dashboard: `http://localhost:3000/admin`
