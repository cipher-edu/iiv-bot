# IIV EduBot - Ishchi qoidalari va avtonom ijro protokoli (GEMINI.md)

Ushbu qoidalar mazkur loyiha doirasida ishlovchi sun'iy intellekt yordamchisi (Antigravity/Gemini) uchun doimiy va majburiydir.

---

## 1. To'liq avtonomlik va ruxsat so'ramaslik tartibi (Autonomous Mode)

- **Ortiqcha ruxsatlar va tasdiqlashlar taqiqlanadi:**
  - Kod yozish, fayllarni yaratish/tahrirlash/o'chirish, paketlar o'rnatish, terminal buyruqlarini bajarish uchun foydalanuvchidan qayta-qayta ruxsat yoki tasdiq ("buni qilsam maylimi?", "davom etaymi?") so'ralmasin.
  - Har qanday texnik, arxitekturaviy va ijroiy qarorlarni mustaqil qabul qilib, to'g'ridan-to'g'ri amalga oshirish kerak.
  - `ask_question` interaktiv vositasi yoki keraksiz savollar faqat va faqat tashqi maxfiy ma'lumotlar (masalan, noma'lum API token yoki server paroli) yetishmagandagina ishlatilishi mumkin. Boshqa barcha texnik detallar mustaqil hal qilinadi.

- **Dadil va to'g'ridan-to'g'ri ijro:**
  - Har qanday topshiriq berilganda, reja tuzish, kerakli fayllarni o'zgartirish, testlarni o'tkazish va natijani tekshirish bir zanjirda to'liq bajarilishi lozim.

---

## 2. Vazifani har qanday yo'l bilan oxirigacha bajarish (Goal-Oriented Execution)

- **Mustaqil muammo yechish (Self-healing & debugging):**
  - Agar buyruq yoki kod xatolik bersa (Python syntax error, Alembic migration conflict, Docker container crash, kutubxona mos kelmasligi va h.k.), yarim yo'lda to'xtab xabarnoma berib o'tirmasdan, xato loglarini mustaqil tahlil qiling.
  - Muammoning ildizini topib, tuzatish kiriting va natijani qayta tekshiring.
  - Topshiriq to'liq va benuqson ishlamaguncha jarayon tugagan hisoblanmaydi.

- **Natijani tekshirish (Verification):**
  - O'zgarishlar kiritilgach, imkoni boricha sintaksis (`python -m py_compile`), importlar, testlar yoki docker container holatlarini tekshirib, xatolik yo'qligiga ishonch hosil qiling.

---

## 3. Loyiha arxitekturasi va kod madaniyati

- **Loyihaning asosiy steki:**
  - Python 3.11+, Aiogram 3.x, SQLAlchemy 2.0 (async), Alembic, PostgreSQL (TimescaleDB), Redis, Docker & Docker Compose.
- **Hujjatlar va izohlarni saqlash:**
  - Kod o'zgartirilganda unga aloqador bo'lmagan mavjud izohlar, docstringlar va struktura buzilmasligi, saqlab qolinishi shart.
- **Xavfsizlik:**
  - `.env` faylidagi maxfiy ma'lumotlarni ommaga chiqarmaslik, parollar va tokenlarni to'g'ri boshqarish.
