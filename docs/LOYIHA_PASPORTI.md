# IIV EDUBOT axborot tizimini yaratish bo'yicha

# LOYIHA PASPORTI

**Hujjat raqami:** IIV-EDUBOT-LP-01

**Tasdiqlash sanasi:** 2026-yil ___-may

---

**TASDIQLAYMAN**

O'zbekiston Respublikasi Ichki ishlar vazirligi
Akademiyasining (yoki muvofiq tashkilot) rahbari

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

(imzo) (F.I.O.)

«___» __________ 2026-yil

M.O'.

---

## 1. Loyiha haqida umumiy ma'lumot

| Ko'rsatkich | Ma'lumot |
|---|---|
| Loyihaning to'liq nomi | Ichki ishlar vazirligi xodimlari va fuqarolari uchun masofaviy ta'lim va malaka oshirish axborot tizimi |
| Loyihaning shartli nomi | IIV EduBot |
| Loyiha turi | Yangi axborot tizimini yaratish |
| Texnologik platforma | Telegram bot, mikroservis arxitekturasi (Docker), bulut/ish-server |
| Ma'lumotlarni qayta ishlash kategoriyasi | Cheklangan kirish (xizmat ma'lumotlari) |
| Loyihaning ko'lami | Idoraviy (Ichki ishlar vazirligi miqyosida) |
| Loyihani amalga oshirish bosqichi | Loyihalash va ishlab chiqish |

## 2. Buyurtmachi va ishlab chiquvchi

### 2.1. Buyurtmachi

| Ma'lumot | Qiymat |
|---|---|
| Tashkilot nomi | O'zbekiston Respublikasi Ichki ishlar vazirligi Akademiyasi (yoki muvofiq tashkilot) |
| Yuridik manzil | \[buyurtma rasmiylashtirilganda kiritiladi] |
| INN | \[buyurtma rasmiylashtirilganda kiritiladi] |
| Aloqa shaxs (F.I.O., lavozim) | \[buyurtma rasmiylashtirilganda kiritiladi] |
| Telefon | \[buyurtma rasmiylashtirilganda kiritiladi] |
| Elektron pochta | \[buyurtma rasmiylashtirilganda kiritiladi] |

### 2.2. Ishlab chiquvchi

| Ma'lumot | Qiymat |
|---|---|
| Tashkilot nomi | \[shartnoma asosida aniqlanadi] |
| Reestr raqami (IT-kompaniya) | \[shartnoma asosida aniqlanadi] |
| Yuridik manzil | \[shartnoma asosida aniqlanadi] |
| Aloqa shaxs | \[shartnoma asosida aniqlanadi] |

## 3. Loyihaning maqsadi va vazifalari

### 3.1. Asosiy maqsad

IIV xodimlari va fuqarolarining masofaviy ta'lim olishi, malaka oshirishi va kasbiy bilim darajasini ob'ektiv baholash uchun yagona avtomatlashtirilgan platforma yaratish.

### 3.2. Loyiha vazifalari

1. Telegram messengeri orqali ishlaydigan ta'lim platformasini ishlab chiqish va joylashtirish.
2. Hodim va Fuqaro toifalari uchun moslashuvchan ro'yxatdan o'tish jarayonini ta'minlash.
3. Kurslar, modullar va darslarni multimedia (video, PDF, audio, havola) bilan boyitish.
4. Avtomatlashtirilgan testlash va sertifikatlash tizimini yaratish.
5. QR kod orqali sertifikatning haqiqiyligini tasdiqlash imkoniyatini qo'shish.
6. Foydalanuvchi faolligini rag'batlantiruvchi gamifikatsiya elementlarini joriy etish.
7. Ma'mur paneli va statistika dashboardi orqali boshqaruv samaradorligini oshirish.
8. Ma'lumotlar xavfsizligi va audit jurnalini ta'minlash.

## 4. Loyihaning amalga oshirish muddatlari

| Bosqich | Boshlanish sanasi | Tugatish sanasi |
|---|---|---|
| Axborotlashtirish ob'ektini tadqiq qilish | 2026-06-01 | 2026-06-15 |
| Tizimni yaratish konsepsiyasi | 2026-06-16 | 2026-06-30 |
| Texnik topshiriq | 2026-07-01 | 2026-07-10 |
| Eskiz loyihasi | 2026-07-11 | 2026-07-25 |
| Texnik loyiha | 2026-07-26 | 2026-08-31 |
| Ishchi loyiha (ishlab chiqish) | 2026-09-01 | 2026-10-31 |
| Hujjatlashtirish va sinovlar | 2026-11-01 | 2026-11-30 |
| Sinov ekspluatatsiyasi | 2026-12-01 | 2026-12-20 |
| Doimiy ekspluatatsiyaga qabul | 2026-12-21 | 2026-12-31 |
| Kafolat muddati | 2027-01-01 | 2027-12-31 |

**Umumiy muddati:** 7 oy (loyihalash + ishlab chiqish + ishga tushirish), 12 oy (kafolat).

## 5. Moliyalashtirish

| Bosqich | Taxminiy harajat (so'm) | Manba |
|---|---|---|
| Loyihalash va ishlab chiqish | \[shartnomada belgilanadi] | Buyurtmachi byudjeti |
| Apparat ta'minoti (server, tarmoq) | \[shartnomada belgilanadi] | Buyurtmachi byudjeti |
| Litsenziya va API to'lovlari (Anthropic/OpenAI) | yiliga 5 000 — 15 000 USD | Buyurtmachi byudjeti |
| Ekspluatatsiya (yiliga, 3 yil davomida) | \[shartnomada belgilanadi] | Buyurtmachi byudjeti |
| **Jami** | \[shartnomada belgilanadi] | — |

Aniq summalar tender va shartnoma natijasiga ko'ra belgilanadi.

## 6. Texnik xarakteristikalar

### 6.1. Tizim arxitekturasi

- Mikroservis arxitekturasi, Docker konteynerlarida.
- Asosiy komponentlar: Bot servisi (Python/aiogram), PostgreSQL DB, Redis, MinIO, Nginx (teskari proksi), monitoring stek (Prometheus + Grafana + Loki).
- Polling rejimida ishlaydi (webhook talab qilmaydi, lekin keyinchalik webhook'ga o'tish imkoni bor).

### 6.2. Foydalanuvchi qismi

- Foydalanuvchi tipi: Telegram messengeri (mobil, desktop, web).
- Interfeys tili: o'zbek tili (lotin yozuvi).
- Maxsus ilovalar talab qilinmaydi.

### 6.3. Server qismi

| Komponent | Talab |
|---|---|
| Operatsion tizim | Ubuntu 22.04 LTS yoki Debian 12 |
| Konteynerlash | Docker 24+, Docker Compose v2 |
| Protsessor | 4 vCPU 2,5 GHz dan kam emas |
| Operativ xotira | 8 GB |
| Saqlash xotirasi | 100 GB SSD (NVMe afzal) |
| Tarmoq | 100 Mbit/s, 2 ta provayder (zaxira bilan) |
| UPS | 30 daqiqalik zaxira ta'minot |

### 6.4. Quvvatga qo'yiladigan talablar

| Ko'rsatkich | Qiymat |
|---|---|
| Bir vaqtning o'zida foydalanuvchilar | 1 000 nafargacha |
| Umumiy ro'yxatdan o'tgan foydalanuvchilar | 50 000 nafargacha |
| Telegramdagi javob vaqti | 1 sekunddan kam (95-foiz) |
| 1 000 ga broadcast | 60 sekunddan kam |
| Tizim mavjudligi | 99,5% (yiliga) |

## 7. Kutilayotgan natijalar

### 7.1. Miqdoriy ko'rsatkichlar

| Ko'rsatkich | Maqsadli qiymat (1-yil) |
|---|---|
| Doimiy foydalanuvchilar | 1 000 nafardan kam emas |
| Tugatilgan kurslar | 5 000 dan kam emas |
| Berilgan elektron sertifikatlar | 3 000 dan kam emas |
| O'rtacha test natijasi | 70% va undan yuqori |
| O'qishga sarflanadigan vaqtning kamayishi | kamida 40% |
| Materiallarning tarqatilish tezligi (yangi e'lon → barcha xodimga) | 1 daqiqadan kam |

### 7.2. Sifat ko'rsatkichlari

- Bilim baholashning ob'ektivligi (testlar avtomatik baholanadi, sub'ektivlik nolga teng).
- Ta'lim materiallarining yagona joyda saqlanishi (tarqalish va eskirish muammosi yo'q).
- Sertifikatlarning soxtalashtirilish ehtimoli nolga teng (QR kod orqali tekshiriladi).
- Foydalanuvchi qoniqishi (so'rovnomalar bo'yicha) — 5 ballik shkala bo'yicha o'rtacha 4,0 dan kam emas.

## 8. Loyihaning samaradorligi

### 8.1. Iqtisodiy samara

- Auditoriya darslari uchun sarflanadigan ish vaqti va yo'l xarajatlarining kamayishi: yiliga taxminan 1 000 — 2 000 ish kunini tejash.
- Qog'oz materiallar va printer xarajatlarining kamayishi.
- Tashkilotning ta'limga moslashuvchanligi oshishi (yangi qoida e'lon qilingan kuni xodimlarga taqdim etish imkoniyati).

### 8.2. Tashkiliy samara

- Xodimlarning bilim darajasi to'g'risida real ma'lumotlar (rahbariyat statistikani Grafana orqali kuzatadi).
- Eng zaif joylarni aniqlash imkoniyati (qaysi mavzularda ko'p xato qilinadi).
- Xodimlarning shaxsiy rivojlanish trayektoriyasini kuzatish.

### 8.3. Ijtimoiy samara

- Fuqarolarga huquqiy va kasbiy mavzularda ochiq ta'lim imkoniyati.
- Xodimlarning malaka darajasi oshishi natijasida xizmat ko'rsatish sifatining yaxshilanishi.

## 9. Riskni baholash

| Risk | Ehtimoli | Ta'siri | Kamaytirish chorasi |
|---|---|---|---|
| Telegram messengerining cheklov yoki bloklanishi | Past | Yuqori | Webhook rejimi va REST API alternativasi tayyorlash |
| Apparat nosozliklari | O'rtacha | O'rtacha | UPS, generator, kunlik backup, ikkinchi server |
| Ma'lumotlarning yo'qotilishi | Past | Yuqori | Tranzaksion DB, kunlik backup, geo-zaxira |
| Xodimlarning yangi tizimga moslashmasligi | O'rtacha | O'rtacha | O'qitish dasturi, yo'riqnomalar, video darslar |
| Maxfiy ma'lumotlarning sizib chiqishi | Past | Yuqori | TLS shifrlash, kirish nazorati, audit |
| AI API litsenziyasining qimmatlashishi | O'rtacha | Past | Ikki API (Anthropic + OpenAI), ichki AI ga o'tish imkoniyati |
| Pul mablag'larining yetishmasligi | Past | Yuqori | Bosqichlarga bo'lib moliyalashtirish, shartnomada belgilash |

## 10. Hujjatlar

| Hujjat | Status | Mas'ul |
|---|---|---|
| Texnik topshiriq | Ishlab chiqilmoqda | Ishlab chiquvchi |
| Loyihaning konsepsiyasi | Tasdiqlangan | Buyurtmachi |
| Texnik loyiha | Loyihalashtirish bosqichida ishlab chiqiladi | Ishlab chiquvchi |
| Foydalanuvchi qo'llanmasi | Ishlab chiqish bosqichida tayyorlanadi | Ishlab chiquvchi |
| Ma'mur qo'llanmasi | Ishlab chiqish bosqichida tayyorlanadi | Ishlab chiquvchi |
| Sinov dasturi va metodikasi | Sinov bosqichidan oldin tayyorlanadi | Buyurtmachi va ishlab chiquvchi birgalikda |

## 11. Loyiha bo'yicha asosiy qaror qabul qiluvchilar

| Lavozim | F.I.O. | Roli |
|---|---|---|
| Buyurtmachi rahbari | \[kiritiladi] | Tasdiqlovchi shaxs |
| Loyiha rahbari (buyurtmachi tomonidan) | \[kiritiladi] | Loyihaning umumiy nazoratchisi |
| Loyiha rahbari (ishlab chiquvchi tomonidan) | \[kiritiladi] | Texnik bajaruvchi |
| Bosh dasturchi | \[kiritiladi] | Arxitektor |
| Sifat menejeri | \[kiritiladi] | Sinov va qabul qilishni nazorat qiladi |
| Axborot xavfsizligi mas'uli | \[kiritiladi] | Xavfsizlik talablari nazorati |

## 12. Asosiy normativ-huquqiy hujjatlar

1. O'zbekiston Respublikasi Prezidentining 2020-yil 5-oktabrdagi PF-6079-son «Raqamli O'zbekiston — 2030» strategiyasini tasdiqlash to'g'risidagi Farmoni.
2. O'zbekiston Respublikasining «Axborotlashtirish to'g'risida»gi Qonuni.
3. O'zbekiston Respublikasining «Shaxsiy ma'lumotlar to'g'risida»gi Qonuni.
4. Vazirlar Mahkamasining 2005-yil 22-noyabrdagi 256-son qaroriga 2-ilova («Davlat organlarining axborot tizimlarini yaratish to'g'risidagi nizom»).
5. Vazirlar Mahkamasining 2007-yil 7-iyundagi 110-son qaroriga 1-ilova («Investitsiya loyihalari hujjatlarini ishlab chiqish, ekspertizadan o'tkazish va tasdiqlash tartibi to'g'risida nizom»).
6. O'z DSt 1986:2018 — Axborot tizimlarini yaratish bosqichlari.
7. O'z DSt 1987:2018 — Axborot tizimini yaratish uchun texnik topshiriq.
8. O'z DSt 1985:20\_\_ — Axborot tizimlarini yaratishda hujjatlar.
9. O'z DSt ISO/IEC 12207:2018 — Dasturiy ta'minot hayotiy tsiklining jarayonlari.
10. O'z DSt 2814:2014 — Avtomatlashtirilgan tizimlar. Axborotni ruxsatsiz foydalana olishdan muhofaza qilish.

---

**Loyiha pasportini ishlab chiqdi:**

Lavozim: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

F.I.O.: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Imzo: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Sana: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Loyiha pasporti tasdiqlandi:**

Lavozim: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

F.I.O.: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Imzo: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Sana: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

M.O'.
