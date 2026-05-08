# IIV EduBot Platform — Bajarilgan ishlar

**Sana:** 2026-05-08

---

## 1. Loyihani ishga tushirish (Docker)

### `.env` fayli yaratildi
- Bot token: `8572744573:AAHQy8HZ8BA-C1Ws8yc_vOHxurgCUVXtqJE`
- Admin ID: `1062838548` (superadmin)
- PostgreSQL, Redis, MinIO, pgAdmin, Grafana konfiguratsiyalari
- Xavfsizlik kalitlari (SECRET_KEY, JWT_SECRET, ENCRYPTION_KEY)
- Scheduler, scoring, notification sozlamalari

### Docker Compose xizmatlari ishga tushirildi (12 ta servis)
- **bot** — Telegram bot (aiogram 3.x)
- **postgres** — TimescaleDB (PostgreSQL)
- **redis** — FSM storage va kesh
- **pgadmin** — Database boshqaruv paneli
- **grafana** — Monitoring dashboard
- **prometheus** — Metrikalar yig'ish
- **loki** — Log yig'ish
- **minio** — Fayl saqlash (S3-compatible)
- **nginx** — Reverse proxy
- **watchtower** — Konteyner yangilash
- **backup** — Avtomatik zaxira nusxa

---

## 2. Xatolar tuzatildi

### 2.1. Pydantic-settings JSON parsing xatosi
- **Muammo:** `ALLOWED_IPS`, `BOT_ADMIN_IDS`, `BOT_SUPERADMIN_IDS` qiymatlari noto'g'ri formatda edi
- **Yechim:** JSON array formatiga o'tkazildi: `[1062838548]`, `["127.0.0.1","172.20.0.0/16"]`

### 2.2. SQLAlchemy `metadata` reserved attribute
- **Muammo:** `bot/models/notification.py` faylida `metadata` ustun nomi SQLAlchemy tomonidan zaxiralangan
- **Yechim:** `metadata` → `extra_data` ga o'zgartirildi (30-qator)

### 2.3. `seed_data.py` import xatosi
- **Muammo:** `from bot.models.base import async_engine` — `async_engine` mavjud emas
- **Yechim:** `from bot.models.base import engine, Base` ga to'g'irlandi (8-qator)

### 2.4. KRITIK: Barcha tugmalar ishlamadi
- **Muammo:** Bot menyusidagi tugmalar (Testlar, Kurslar, Yangiliklar, Reyting va h.k.) bosilganda hech narsa sodir bo'lmadi
- **Sabab:** aiogram 3.x middleware arxitekturasi — `dp.message.middleware()` orqali ro'yxatdan o'tkazilgan middleware'lar child router'lardagi `IsRegisteredFilter` filtrlari oldidan ishlamadi
- **Yechim:** `bot/main.py` faylida middleware'lar qayta tashkil qilindi:
  - `ErrorHandlerMiddleware` va `MaintenanceMiddleware` → `dp.message.outer_middleware()` / `dp.callback_query.outer_middleware()`
  - `DatabaseSessionMiddleware`, `ThrottlingMiddleware`, `AuthMiddleware`, `BanCheckMiddleware`, `I18nMiddleware`, `AuditLogMiddleware` → `root_router.message.outer_middleware()` / `root_router.callback_query.outer_middleware()`
- **Fayl:** `bot/main.py` (97-112 qatorlar)

### 2.5. Foydalanuvchi roli
- **Muammo:** Foydalanuvchi USER rolida ro'yxatdan o'tgan, lekin SUPERADMIN kerak edi
- **Yechim:** SQL orqali: `UPDATE users SET role='superadmin' WHERE telegram_id=1062838548`

---

## 3. Demo ma'lumotlar bazaga yuklandi

### `scripts/seed_demo.sql` yaratildi va ishga tushirildi

| Ma'lumot turi | Soni | Tafsilot |
|---|---|---|
| Tashkilotlar | 10 | 3 bo'lim, 3 fakultet, 3 kafedra + root |
| Fayl kategoriyalari | 6 | Darslik, Lektsiya, Amaliyot, Video, Prezentatsiya, Boshqa |
| Badge (yutuqlar) | 10 | Barcha BadgeType enum qiymatlari |
| Testlar | 4 | Kiberxavfsizlik asoslari, Tarmoq xavfsizligi, Kriptografiya, Axborot xavfsizligi qonunchilik |
| Savollar | 16 | Har bir testda 4 ta savol |
| Javob variantlari | 64 | Har bir savolda 4 ta variant (to'g'ri javoblar belgilangan) |
| Kurslar | 4 | Kiberxavfsizlik, Tarmoq xavfsizligi, Kriptografiya, Digital forensika |
| Modullar | 11 | Kurslar ichida tematik bo'limlar |
| Darslar | 22 | Batafsil kiberxavfsizlik ta'lim materiallari |
| Yangiliklar | 6 | Turli mavzularda yangilik maqolalari |
| Challenge (musobaqa) | 3 | Faol musobaqalar |
| So'rovnomalar | 2 | 5 ta savol bilan |
| Topshiriqlar | 3 | Turli mavzularda |
| Foydalanuvchi ma'lumotlari | 1 | Reyting, daraja, streak yangilandi |

---

## 4. O'zgartirilgan fayllar ro'yxati

| Fayl | Amal |
|---|---|
| `.env` | Yaratildi — barcha muhit o'zgaruvchilari |
| `bot/main.py` | Tahrirlandi — middleware ro'yxatdan o'tkazish tartibi tuzatildi |
| `bot/models/notification.py` | Tahrirlandi — `metadata` → `extra_data` |
| `bot/middlewares/db_session.py` | Tahrirlandi — soddalashtirildi |
| `scripts/seed_data.py` | Tahrirlandi — import tuzatildi |
| `scripts/seed_demo.sql` | Yaratildi — demo ma'lumotlar (SQL) |

---

## 5. Muhim texnik eslatmalar

1. **aiogram 3.x middleware tartibi:** Router-level filterlar ishlashi uchun middleware'lar `root_router.outer_middleware()` orqali ro'yxatdan o'tkazilishi kerak, `dp.middleware()` emas
2. **Pydantic-settings:** `.env` faylidagi list turidagi maydonlar JSON formatida bo'lishi kerak
3. **SQLAlchemy:** `metadata` nomi model ustunlari uchun ishlatilmasligi kerak (zaxiralangan)
4. **Docker:** `.env` o'zgarishlaridan keyin `--force-recreate` kerak (konteyner qayta yaratilishi lozim)
5. **Demo ma'lumotlar:** ID'lar 100 dan boshlanadi (mavjud ma'lumotlar bilan to'qnashmaslik uchun), `ON CONFLICT DO NOTHING` xavfsizlik uchun ishlatiladi
