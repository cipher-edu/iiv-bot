# IIV EduBot

Ichki ishlar vazirligi xodimlari va fuqarolari uchun ta'lim platformasi. Telegram bot orqali kurslar, testlar, sertifikatlar, reyting va boshqa o'qish vositalarini taqdim etadi.

## Loyiha haqida

Platforma asosan Uzbekistan IIV Akademiyasi va undagi tashkilotlar — fakultetlar, kafedralar, bo'limlar uchun mo'ljallangan, lekin oddiy fuqarolar ham ro'yxatdan o'tib foydalanishi mumkin. Tizim ikki turdagi foydalanuvchini ajratadi:

- **Hodim** — tashkilotda ishlovchi, lavozim va tashkilot ma'lumotlari bilan
- **Fuqaro** — oddiy foydalanuvchi, faqat ism-familiya kiritadi

Adminlar kurslar yaratadi, foydalanuvchilarni boshqaradi, broadcast yuboradi. Super admin esa rollarni tayinlaydi, audit log'ni ko'radi va tizim sozlamalarini boshqaradi.

## Asosiy imkoniyatlar

### Foydalanuvchi tomoni

- Bosqichma-bosqich ro'yxatdan o'tish (telefon, F.I.O, toifa)
- Kurslar, modullar, darslar — har biri matn, video, PDF, audio yoki tashqi havola bilan
- Har bir kurs uchun sillabus
- Darsni yakunlagandan keyin majburiy 1-5 yulduzli baholash
- Test topshirish (vaqt cheklovi, ko'p marta urinish)
- Sertifikat olish va PDF yuklash (QR kod orqali tasdiqlash)
- Reyting tizimi, yutuqlar, badge va daraja
- Kunlik streak (har 7 kunlik faollik uchun bonus ball)
- Shaxsiy maqsadlar (haftalik/oylik)
- Spaced repetition — o'tilgan darsni avtomatik takrorlash
- Saqlanganlar (bookmark)
- Q&A — har bir dars ostida savol-javob
- Kutubxona — fayllarni yuklab olish
- AI yordamchi (Anthropic Claude yoki OpenAI)
- Yangiliklar va anketalar
- Bildirishnoma sozlamalari (qaysi turlarini olish)
- Anonim taklif/shikoyat yuborish

### Admin tomoni

- Foydalanuvchilarni boshqarish (ro'yxat, qidiruv, rollar)
- Bloklash (1 soat / 1 kun / 7 kun / 30 kun / muddatsiz) sabab bilan
- Foydalanuvchiga blok haqida avtomatik xabar
- Kurs yaratish (qoralama → e'lon qilish), modullar, darslar
- Darsga material (video, PDF, havola) qo'shish
- AI orqali test savollari generatsiyasi
- Test va anketa tuzish
- Broadcast — barchaga yoki segment bo'yicha (tashkilot, rol, ball miqdori)
- Sertifikat berish (avtomatik PDF + QR kod)
- Statistika dashboard'i (faollik, drop-off, top kurslar)
- Excel/CSV import (foydalanuvchilarni ommaviy yuklash)
- Audit log brauzeri

### Super admin

- `.env` faylida belgilangan, doimiy huquqqa ega
- Yangi adminlarni bot orqali tayinlash (Telegram ID kiritib)
- Takliflar inboxi
- Audit log tarixi
- Tizim holati va backuplar

### Texnik xususiyatlar

- Polling rejimida ishlaydi (webhook talab qilmaydi)
- Telegram API rate limit'ga rioya (28 msg/sec global, 1 msg/sec per chat)
- Avtomatik retry (TelegramRetryAfter va network xatolarida)
- Background broadcast queue (asosiy oqim bloklanmaydi)
- Redis cache layer (xato bo'lganda graceful fallback)
- Heartbeat fayl + Docker healthcheck
- Graceful shutdown (SIGTERM)

## Texnologiyalar

| Sohasi | Texnologiya |
|---|---|
| Bot framework | aiogram 3.7 (asynchronous) |
| Web framework | aiohttp (webhook server) |
| Tilga | Python 3.11 |
| Ma'lumotlar bazasi | PostgreSQL 15 (TimescaleDB extension bilan) |
| ORM | SQLAlchemy 2.0 (async) |
| Cache va FSM | Redis 7 |
| Fayl xotirasi | MinIO (S3-compatible) |
| Scheduler | APScheduler |
| AI | Anthropic Claude / OpenAI |
| PDF | ReportLab |
| Excel | openpyxl |
| Monitoring | Prometheus + Grafana + Loki |
| Web admin | pgAdmin |
| Konteynerlash | Docker Compose |
| Reverse proxy | Nginx |

## Loyiha tuzilishi

```
iiv bot/
├── bot/
│   ├── core/              # Asosiy yordamchi modullar (cache, rate limit, queue)
│   ├── config.py          # Pydantic settings
│   ├── filters/           # aiogram filterlari (admin, registered, role)
│   ├── handlers/          # Botni ishlash mantig'i
│   │   ├── user/         # Foydalanuvchi handlerlari
│   │   ├── admin/        # Admin handlerlari
│   │   ├── superadmin/   # Super admin handlerlari
│   │   └── moderator/    # Moderator handlerlari
│   ├── integrations/      # Tashqi xizmatlar (AI, MinIO, SMTP)
│   ├── keyboards/         # Inline va reply klaviaturalar
│   ├── middlewares/       # Auth, ban check, rate limit, audit
│   ├── models/            # SQLAlchemy modellari
│   ├── repositories/      # Ma'lumotlar bazasi qatlami
│   ├── scheduler/         # Cron vazifalar
│   ├── services/          # Biznes mantiq
│   ├── states/            # FSM holatlar
│   ├── security/          # Bruteforce, encryption, sanitizer
│   ├── utils/             # Yordamchi funksiyalar (PDF, logger)
│   └── main.py            # Kirish nuqtasi
├── nginx/                 # Nginx konfiguratsiyasi
├── monitoring/            # Prometheus, Grafana, Loki konfiguratsiyalari
├── scripts/               # Yordamchi skriptlar (seeder, healthcheck)
├── docker-compose.yml     # Konteyner orkestratsiyasi
├── Dockerfile             # Bot konteyneri
├── requirements.txt       # Python kutubxonalari
├── .env                   # Maxfiy konfiguratsiya (push qilinmaydi normalda)
├── .env.example           # .env namunasi
├── start.bat              # Windows: bir marta bosib ishga tushirish
├── stop.bat               # Windows: to'xtatish
└── logs.bat               # Windows: jonli loglarni ko'rish
```

## O'rnatish

### Talablar

- Docker Desktop (Windows uchun) yoki Docker Engine + Compose (Linux/Mac)
- Bo'sh joy: kamida 5 GB
- RAM: kamida 4 GB tavsiya etiladi

### Birinchi marta ishga tushirish

1. Loyihani klonlash:

   ```bash
   git clone https://github.com/cipher-edu/iiv-bot.git
   cd iiv-bot
   ```

2. `.env` faylini sozlash:

   ```bash
   cp .env.example .env
   ```

   `.env` faylini ochib quyidagilarni to'ldiring:

   - `BOT_TOKEN` — @BotFather'dan olingan token
   - `BOT_ADMIN_IDS` — admin Telegram ID'lari
   - `BOT_SUPERADMIN_IDS` — super admin Telegram ID'lari
   - `DB_PASSWORD`, `REDIS_PASSWORD`, `MINIO_PASSWORD` — kuchli parollar
   - `SECRET_KEY`, `ENCRYPTION_KEY`, `JWT_SECRET` — tasodifiy uzun kalitlar
   - `ANTHROPIC_API_KEY` yoki `OPENAI_API_KEY` — AI funksiyalar uchun (ixtiyoriy)

3. Konteynerlarni ishga tushirish:

   **Windows:**
   ```
   start.bat ga ikki marta bosing
   ```

   **Linux/Mac yoki qo'lda:**
   ```bash
   docker compose -p iiv-bot up -d
   ```

4. Botning Telegram'da ochib `/start` bosing — ro'yxatdan o'tish jarayoni boshlanadi.

### Demo ma'lumotlar yuklash

Test maqsadida har bir jadvalga 10 dan ortiq yozuv yuklash uchun:

```bash
docker exec iiv_bot python /app/scripts/seed_demo.py
```

Bu skript idempotent — qayta ishga tushirilsa, dublikat yaratmaydi.

## Servis manzillari

Loyiha ishga tushgandan keyin quyidagi servislar mavjud bo'ladi:

| Servis | URL | Default login |
|---|---|---|
| Bot | Telegramda `/start` | — |
| Grafana | http://localhost:3000 | admin / `.env`'dagi `GRAFANA_ADMIN_PASSWORD` |
| pgAdmin | http://localhost:5050 | `.env`'dagi `PGADMIN_EMAIL` / `PGADMIN_PASSWORD` |
| MinIO konsoli | http://localhost:9001 | `MINIO_USER` / `MINIO_PASSWORD` |
| Prometheus | http://localhost:9090 | — |
| Nginx (reverse proxy) | http://localhost:8080 | — |

## Boshqaruv

### Ishga tushirish

```bash
docker compose -p iiv-bot up -d
```

Yoki Windows'da: `start.bat`.

### To'xtatish

```bash
docker compose -p iiv-bot stop
```

Yoki Windows'da: `stop.bat`. Bu konteynerlarni to'xtatadi, lekin volume'larni saqlab qoladi (ma'lumotlar yo'qolmaydi).

### Loglarni kuzatish

```bash
docker logs -f iiv_bot
```

Yoki Windows'da: `logs.bat`.

### Faqat botni qayta ishga tushirish

```bash
docker compose -p iiv-bot restart bot
```

### Kodni o'zgartirgandan keyin qayta build

```bash
docker compose -p iiv-bot build bot
docker compose -p iiv-bot up -d bot
```

### Ma'lumotlar bazasi backup

```bash
docker exec iiv_postgres pg_dump -U iiv_admin iiv_bot > backup.sql
```

Avtomatik backup `iiv_backup` konteyneri tomonidan kuniga bir marta amalga oshiriladi (saqlash papkasi: `./backups/`).

## Foydalanuvchi rollari

Tizimda 5 ta rol bor:

| Rol | Ruxsatlar |
|---|---|
| `superadmin` | Hammasi: rollar, sozlamalar, audit, takliflar |
| `admin` | Kurslar, testlar, foydalanuvchilar, broadcast, statistika |
| `moderator` | Kontentni nazorat qilish (Q&A javoblari rasmiy belgilanadi) |
| `user` | Oddiy foydalanuvchi |
| `guest` | Ro'yxatdan o'tmagan |

Super admin `.env` faylida belgilanadi va tizim har ishga tushganda DB bilan sinxronlanadi. Boshqa adminlarni super admin tayinlaydi (Telegram ID kiritish orqali).

## Konfiguratsiya

Asosiy parametrlar `.env` faylida. To'liq ro'yxat va tushuntirishlar `.env.example`'da. Eng muhimlari:

| O'zgaruvchi | Tavsifi | Standart |
|---|---|---|
| `BOT_TOKEN` | Telegram bot tokeni | — |
| `BOT_SUPERADMIN_IDS` | Super admin Telegram ID'lari | — |
| `DB_POOL_SIZE` | PostgreSQL connection pool | 20 |
| `MAX_FILE_SIZE_MB` | Yuklanadigan fayl maksimal hajmi | 50 |
| `RATE_LIMIT_USER` | Foydalanuvchi uchun so'rovlar/daqiqa | 30 |
| `BAN_DURATION_MINUTES` | Brute force qilganlar uchun blok muddati | 15 |
| `QUIET_HOURS_START` / `QUIET_HOURS_END` | Tinch soatlar (bildirishnoma yuborilmaydi) | 22 / 7 |
| `AI_ENABLED` | AI funksiyalari yoqilganmi | false |

## Ma'lumotlar bazasi sxemasi

50+ jadval bor. Asosiy guruhlar:

- **users** — foydalanuvchilar va `organizations` (tashkilotlar)
- **courses** — kurslar, `course_modules`, `lessons`, `lesson_attachments`, `lesson_ratings`, `lesson_history`, `course_prerequisites`, `enrollments`, `lesson_progress`
- **tests** — testlar, `questions`, `answer_options`, `test_sessions`, `user_answers`, `test_results`
- **gamifikatsiya** — `badges`, `user_badges`, `user_streaks`, `user_levels`, `challenges`, `challenge_participations`, `user_goals`
- **rating** — `user_ratings`, `point_transactions`, `weekly_leaderboards`
- **kontent** — `news`, `library`, `surveys`, `tasks`, `notifications`, `ai_conversations`
- **xavfsizlik** — `audit_logs`, `security_events`
- **yangi imkoniyatlar** — `saved_items`, `suggestions`, `learning_paths`, `lesson_questions`, `lesson_answers`, `spaced_repetition`

Sxema o'zgarishlari `bot/models/migrations.py` orqali idempotent qo'llaniladi (additive only — yangi ustun va indekslar). Kelajakda Alembic migratsiyalariga o'tish rejalashtirilgan.

## Monitoring

- **Grafana** dashboardlari `monitoring/grafana/provisioning/` da
- **Prometheus** metricalari `bot/services/security_service.py` orqali (qisman) eksport qilinadi
- **Loki** botning structlog'dan keladigan loglarni yig'adi
- **Watchtower** Docker imagelarini avtomatik yangilaydi (kuniga 04:00 da tekshiradi)

Agar bot 2 daqiqada heartbeat fayl yangilanmasa, Docker uni `unhealthy` deb belgilaydi va qayta ishga tushiradi.

## Xavfsizlik

- Barcha parollar `.env` faylida (production'da `git`'ga tushmasligi kerak)
- Brute force protection — `MAX_LOGIN_ATTEMPTS` urinishdan keyin foydalanuvchi avtomatik bloklanadi
- Bloklangan foydalanuvchilar `BanCheckMiddleware` orqali to'sib qo'yiladi
- Audit log barcha muhim amallarni yozib boradi (login, blok, rol o'zgartirish, broadcast va boshqalar)
- Super admin DB orqali o'zgartirib bo'lmaydi (har ishga tushganda `.env`'dan tiklanadi)
- Foydalanuvchi kiritmalari sanitizer'dan o'tkaziladi (XSS, SQL injection oldini olish)

## Rivojlanish

Yangi handler qo'shish uchun:

1. `bot/handlers/user/yangi_funksiya.py` faylini yarating
2. `bot/handlers/user/__init__.py`'da router'ni import qiling va include'ga qo'shing
3. Agar yangi DB jadvali kerak bo'lsa: `bot/models/yangi_model.py` yarating va `bot/models/__init__.py`'da import qiling
4. Repository pattern ishlatib, `bot/repositories/yangi_repo.py` yarating
5. Sxema o'zgarishini `bot/models/migrations.py`'ga `ALTER TABLE ... IF NOT EXISTS` shaklida qo'shing
6. Konteynerni qayta build qiling: `docker compose -p iiv-bot build bot && docker compose -p iiv-bot up -d bot`

Kod uslubi: PEP 8, async/await, repository pattern, FSM dialoglarda `aiogram.fsm`.

## Tez-tez uchraydigan muammolar

**Bot konteyneri healthy bo'lmaydi**

```
docker logs iiv_bot --tail 50
```

`/tmp/bot_heartbeat` fayli har 30 soniyada yangilanishi kerak. Agar yo'q bo'lsa, bot main loop crash bo'lgan demakdir.

**Database connection xatolari**

PostgreSQL konteyneri tayyor bo'lishini kuting (healthcheck: `pg_isready`). Bot avtomatik kutadi.

**Permission xatosi MinIO/data papkasida**

```bash
docker exec -u root iiv_bot chown -R botuser:botuser /app/data
```

**Port band**

Agar `5432`, `6379`, `8080` portlari band bo'lsa, `docker-compose.yml`'dagi port mappinglarini o'zgartiring.

## Litsenziya

Loyiha xususiy. Xizmat doirasidan tashqarida qayta tarqatish ruxsat etilmaydi.

## Mualliflik

Loyiha Ichki ishlar vazirligi Akademiyasi uchun ishlab chiqilgan.

Repo: https://github.com/cipher-edu/iiv-bot
