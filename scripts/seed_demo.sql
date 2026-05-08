-- ============================================
-- IIV EDUBOT - Demo Data Seed
-- ============================================

BEGIN;

-- ──── ORGANIZATIONS ────
INSERT INTO organizations (id, name, org_type, is_active, parent_id, is_deleted, created_at, updated_at)
VALUES
  (100, 'Ichki ishlar vazirligi', 'bolim', true, NULL, false, now(), now()),
  (101, 'Kiberxavfsizlik boshqarmasi', 'bolim', true, 100, false, now(), now()),
  (102, 'Axborot texnologiyalari bo''limi', 'bolim', true, 100, false, now(), now()),
  (103, 'Kadrlar bo''limi', 'bolim', true, 100, false, now(), now()),
  (104, 'Huquq fakulteti', 'fakultet', true, NULL, false, now(), now()),
  (105, 'AT fakulteti', 'fakultet', true, NULL, false, now(), now()),
  (106, 'Kriminalistika fakulteti', 'fakultet', true, NULL, false, now(), now()),
  (107, 'Dasturlash kafedrasi', 'kafedra', true, 105, false, now(), now()),
  (108, 'Tarmoq xavfsizligi kafedrasi', 'kafedra', true, 105, false, now(), now()),
  (109, 'Jinoyat huquqi kafedrasi', 'kafedra', true, 104, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('organizations_id_seq', 200);

-- ──── FILE CATEGORIES ────
INSERT INTO file_categories (id, name, description, icon, parent_id, "order", is_active, is_deleted, created_at, updated_at)
VALUES
  (100, 'Qonunchilik', 'Qonunlar va normativ hujjatlar', '📜', NULL, 1, true, false, now(), now()),
  (101, 'Yo''riqnomalar', 'Ichki yo''riqnomalar va buyruqlar', '📋', NULL, 2, true, false, now(), now()),
  (102, 'AT materiallari', 'Axborot texnologiyalari bo''yicha', '💻', NULL, 3, true, false, now(), now()),
  (103, 'Kiberxavfsizlik', 'Xavfsizlik bo''yicha materiallar', '🛡', NULL, 4, true, false, now(), now()),
  (104, 'Video darsliklar', 'O''quv videolari', '🎬', NULL, 5, true, false, now(), now()),
  (105, 'Shablonlar', 'Hujjat shablonlari', '📄', NULL, 6, true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('file_categories_id_seq', 200);

-- ──── BADGES ────
INSERT INTO badges (id, badge_type, name, description, icon, points_reward, is_active, is_deleted, created_at, updated_at)
VALUES
  (100, 'first_test',    'Birinchi qadam',     'Birinchi testni topshirdingiz!', '🎯', 5, true, false, now(), now()),
  (101, 'ten_tests',     'Test ustasi',        '10 ta test topshirdingiz!', '📝', 15, true, false, now(), now()),
  (102, 'perfect_score', 'Mukammal natija',    '100% to''g''ri javob berdingiz!', '💯', 20, true, false, now(), now()),
  (103, 'first_course',  'O''quvchi',          'Birinchi kursni tugatdingiz!', '📚', 10, true, false, now(), now()),
  (104, 'five_courses',  'Bilimdon',           '5 ta kursni muvaffaqiyatli tugatdingiz!', '🎓', 30, true, false, now(), now()),
  (105, 'streak_7',      'Haftalik streak',    '7 kun ketma-ket faol bo''ldingiz!', '🔥', 10, true, false, now(), now()),
  (106, 'streak_30',     'Oylik streak',       '30 kun ketma-ket faol bo''ldingiz!', '⚡', 50, true, false, now(), now()),
  (107, 'top_weekly',    'Hafta yulduzi',      'Haftalik reytingda birinchi o''rin!', '⭐', 25, true, false, now(), now()),
  (108, 'helper',        'Yordamchi',          'Boshqalarga yordam berdingiz!', '🤝', 10, true, false, now(), now()),
  (109, 'early_bird',    'Erta qush',          'Eng birinchilardan bo''lib kirish!', '🌅', 5, true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('badges_id_seq', 200);

-- ──── TESTS ────
-- Test 1: Kiberxavfsizlik asoslari
INSERT INTO tests (id, title, description, time_per_question, passing_score, is_active, randomize_questions, randomize_options, max_attempts, show_correct_answers, is_deleted, created_at, updated_at)
VALUES
  (100, 'Kiberxavfsizlik asoslari', 'Kiberxavfsizlik bo''yicha asosiy bilimlarni tekshirish testi. Fishing, malware, parol xavfsizligi va boshqa muhim mavzular.', 30, 60, true, true, true, 3, false, false, now(), now()),
  (101, 'Axborot xavfsizligi qoidalari', 'IIV xodimlari uchun axborot xavfsizligi qoidalari bo''yicha test.', 25, 70, true, true, true, 2, true, false, now(), now()),
  (102, 'Shaxsiy ma''lumotlarni himoya qilish', 'Shaxsiy ma''lumotlar bilan ishlash tartibini bilish.', 30, 65, true, true, true, 3, false, false, now(), now()),
  (103, 'Tarmoq xavfsizligi', 'Kompyuter tarmoqlari xavfsizligi bo''yicha bilimlarni tekshirish.', 35, 60, true, true, true, 2, true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('tests_id_seq', 200);

-- Test 1 questions
INSERT INTO questions (id, test_id, text, "order", is_active, is_deleted, created_at, updated_at)
VALUES
  (100, 100, 'Fishing (phishing) hujumi nima?', 1, true, false, now(), now()),
  (101, 100, 'Kuchli parol qanday bo''lishi kerak?', 2, true, false, now(), now()),
  (102, 100, 'Ransomware nima?', 3, true, false, now(), now()),
  (103, 100, 'Ikki bosqichli autentifikatsiya (2FA) nima?', 4, true, false, now(), now()),
  (104, 100, 'VPN nima uchun ishlatiladi?', 5, true, false, now(), now()),
  -- Test 2 questions
  (110, 101, 'Maxfiy hujjatlarni qanday saqlash kerak?', 1, true, false, now(), now()),
  (111, 101, 'Ish kompyuterida shaxsiy dasturlar o''rnatish mumkinmi?', 2, true, false, now(), now()),
  (112, 101, 'Parolni necha kunda bir o''zgartirish kerak?', 3, true, false, now(), now()),
  (113, 101, 'Noma''lum jo''natuvchidan kelgan xatni nima qilish kerak?', 4, true, false, now(), now()),
  -- Test 3 questions
  (120, 102, 'Shaxsiy ma''lumotlarga nimalar kiradi?', 1, true, false, now(), now()),
  (121, 102, 'Ma''lumotlarni uchinchi shaxslarga berish uchun nima kerak?', 2, true, false, now(), now()),
  (122, 102, 'Ma''lumotlar buzilishi (data breach) sodir bo''lganda nima qilish kerak?', 3, true, false, now(), now()),
  -- Test 4 questions
  (130, 103, 'Firewall nima vazifani bajaradi?', 1, true, false, now(), now()),
  (131, 103, 'DDoS hujumi nima?', 2, true, false, now(), now()),
  (132, 103, 'HTTPS va HTTP ning farqi nima?', 3, true, false, now(), now()),
  (133, 103, 'Wi-Fi tarmog''ida xavfsizlik uchun nimadan foydalanish kerak?', 4, true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('questions_id_seq', 200);

-- Answer options for Test 1
INSERT INTO answer_options (id, question_id, text, is_correct, "order", is_deleted, created_at, updated_at)
VALUES
  -- Q100: Fishing hujumi
  (1000, 100, 'Virus turi', false, 1, false, now(), now()),
  (1001, 100, 'Foydalanuvchini aldab maxfiy ma''lumotlarini olish hujumi', true, 2, false, now(), now()),
  (1002, 100, 'DDoS hujumi', false, 3, false, now(), now()),
  (1003, 100, 'Brute force hujumi', false, 4, false, now(), now()),
  -- Q101: Kuchli parol
  (1010, 101, 'Faqat raqamlardan iborat', false, 1, false, now(), now()),
  (1011, 101, 'Kamida 12 belgi, katta-kichik harf, raqam va maxsus belgilar', true, 2, false, now(), now()),
  (1012, 101, 'Tug''ilgan sana', false, 3, false, now(), now()),
  (1013, 101, 'Ism va familiya', false, 4, false, now(), now()),
  -- Q102: Ransomware
  (1020, 102, 'Antivirus dasturi', false, 1, false, now(), now()),
  (1021, 102, 'Ma''lumotlarni shifrlash va to''lov talab qiluvchi zararli dastur', true, 2, false, now(), now()),
  (1022, 102, 'Tarmoq skaneri', false, 3, false, now(), now()),
  (1023, 102, 'Xavfsizlik devori', false, 4, false, now(), now()),
  -- Q103: 2FA
  (1030, 103, 'Ikki marta parol kiritish', false, 1, false, now(), now()),
  (1031, 103, 'Ikkita turli xil tasdiqlash usulini qo''llash', true, 2, false, now(), now()),
  (1032, 103, 'Ikki kompyuterdan kirish', false, 3, false, now(), now()),
  (1033, 103, 'Ikki marta login qilish', false, 4, false, now(), now()),
  -- Q104: VPN
  (1040, 104, 'Internetni tezlashtirish uchun', false, 1, false, now(), now()),
  (1041, 104, 'Xavfsiz va shifrlangan aloqa kanali yaratish uchun', true, 2, false, now(), now()),
  (1042, 104, 'Viruslardan himoya uchun', false, 3, false, now(), now()),
  (1043, 104, 'Fayllarni saqlash uchun', false, 4, false, now(), now()),
  -- Test 2 answers
  (1100, 110, 'Stolda ochiq qoldirish', false, 1, false, now(), now()),
  (1101, 110, 'Shifrlangan va kiritish huquqi cheklangan joyda', true, 2, false, now(), now()),
  (1102, 110, 'Shaxsiy telefonda', false, 3, false, now(), now()),
  (1103, 110, 'Bulutli xotiraga yuklash', false, 4, false, now(), now()),
  (1110, 111, 'Ha, istalgan dasturni', false, 1, false, now(), now()),
  (1111, 111, 'Yo''q, faqat ruxsat etilgan dasturlarni', true, 2, false, now(), now()),
  (1112, 111, 'Faqat o''yinlarni', false, 3, false, now(), now()),
  (1113, 111, 'Ha, lekin faqat bepul dasturlarni', false, 4, false, now(), now()),
  (1120, 112, 'Hech qachon o''zgartirmaslik kerak', false, 1, false, now(), now()),
  (1121, 112, 'Har 90 kunda bir marta', true, 2, false, now(), now()),
  (1122, 112, 'Yilda bir marta', false, 3, false, now(), now()),
  (1123, 112, 'Faqat buzilganda', false, 4, false, now(), now()),
  (1130, 113, 'Darhol ochish va o''qish', false, 1, false, now(), now()),
  (1131, 113, 'O''chirish va IT bo''limiga xabar berish', true, 2, false, now(), now()),
  (1132, 113, 'Ilovalarini yuklab olish', false, 3, false, now(), now()),
  (1133, 113, 'Hamkasblaringizga yuborish', false, 4, false, now(), now()),
  -- Test 3 answers
  (1200, 120, 'Faqat ism va familiya', false, 1, false, now(), now()),
  (1201, 120, 'Ism, manzil, telefon, email va boshqa shaxsni identifikatsiya qiluvchi ma''lumotlar', true, 2, false, now(), now()),
  (1202, 120, 'Faqat parol', false, 3, false, now(), now()),
  (1203, 120, 'Faqat moliyaviy ma''lumotlar', false, 4, false, now(), now()),
  (1210, 121, 'Hech narsa kerak emas', false, 1, false, now(), now()),
  (1211, 121, 'Ma''lumot egasining yozma roziligi', true, 2, false, now(), now()),
  (1212, 121, 'Rahbar ruxsati', false, 3, false, now(), now()),
  (1213, 121, 'Telefon orqali so''rash', false, 4, false, now(), now()),
  (1220, 122, 'Hech narsa qilmaslik', false, 1, false, now(), now()),
  (1221, 122, 'Darhol mas''ul shaxslarga xabar berish va hodisani qayd qilish', true, 2, false, now(), now()),
  (1222, 122, 'O''chirib yuborish', false, 3, false, now(), now()),
  (1223, 122, 'Keyinroq tekshirish', false, 4, false, now(), now()),
  -- Test 4 answers
  (1300, 130, 'Internet tezligini oshirish', false, 1, false, now(), now()),
  (1301, 130, 'Tarmoq trafigini nazorat qilish va ruxsatsiz kirishdan himoyalash', true, 2, false, now(), now()),
  (1302, 130, 'Fayllarni saqlash', false, 3, false, now(), now()),
  (1303, 130, 'Email yuborish', false, 4, false, now(), now()),
  (1310, 131, 'Tezkor internet aloqasi', false, 1, false, now(), now()),
  (1311, 131, 'Serverga bir vaqtda ko''p so''rov yuborib ishdan chiqarish hujumi', true, 2, false, now(), now()),
  (1312, 131, 'Parol o''g''irlash', false, 3, false, now(), now()),
  (1313, 131, 'Ma''lumotlarni shifrlash', false, 4, false, now(), now()),
  (1320, 132, 'Farqi yo''q', false, 1, false, now(), now()),
  (1321, 132, 'HTTPS ma''lumotlarni shifrlaydi, HTTP esa shifrlmamaydi', true, 2, false, now(), now()),
  (1322, 132, 'HTTP tezroq ishlaydi', false, 3, false, now(), now()),
  (1323, 132, 'HTTPS faqat banklar uchun', false, 4, false, now(), now()),
  (1330, 133, 'Ochiq tarmoqqa ulanish', false, 1, false, now(), now()),
  (1331, 133, 'WPA3 shifrlash standartidan foydalanish', true, 2, false, now(), now()),
  (1332, 133, 'Parolsiz tarmoq', false, 3, false, now(), now()),
  (1333, 133, 'WEP shifrlash', false, 4, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('answer_options_id_seq', 2000);

-- ──── COURSES ────
INSERT INTO courses (id, title, description, min_points, "order", is_active, difficulty, estimated_hours, is_deleted, created_at, updated_at)
VALUES
  (100, 'Axborot xavfsizligi asoslari', 'IIV xodimlari uchun axborot xavfsizligi asoslari kursi. Tarmoq xavfsizligi, ma''lumotlarni himoyalash va kiberxavfsizlik bo''yicha bilimlar.', 0, 1, true, 'beginner', 10, false, now(), now()),
  (101, 'Kiberxavfsizlik amaliyoti', 'Amaliy kiberxavfsizlik ko''nikmalari. Hujumlarni aniqlash, oldini olish va javob berish.', 30, 2, true, 'intermediate', 15, false, now(), now()),
  (102, 'Shaxsiy ma''lumotlarni himoyalash', 'Fuqarolarning shaxsiy ma''lumotlari bilan ishlash tartibi va qonunchilik.', 0, 3, true, 'beginner', 8, false, now(), now()),
  (103, 'Raqamli kriminalistika', 'Raqamli dalillar bilan ishlash, tahlil qilish va hujjatlashtirish.', 50, 4, true, 'advanced', 20, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('courses_id_seq', 200);

-- Course modules
INSERT INTO course_modules (id, course_id, title, "order", is_deleted, created_at, updated_at)
VALUES
  -- Course 100
  (100, 100, 'Kirish va asosiy tushunchalar', 1, false, now(), now()),
  (101, 100, 'Tahdidlar va zaifliklar', 2, false, now(), now()),
  (102, 100, 'Himoya vositalari', 3, false, now(), now()),
  -- Course 101
  (110, 101, 'Hujum turlari', 1, false, now(), now()),
  (111, 101, 'Monitoring va aniqlash', 2, false, now(), now()),
  (112, 101, 'Hodisalarga javob berish', 3, false, now(), now()),
  -- Course 102
  (120, 102, 'Qonunchilik asoslari', 1, false, now(), now()),
  (121, 102, 'Ma''lumotlar bilan ishlash', 2, false, now(), now()),
  -- Course 103
  (130, 103, 'Raqamli dalillar', 1, false, now(), now()),
  (131, 103, 'Tahlil usullari', 2, false, now(), now()),
  (132, 103, 'Hisobot tayyorlash', 3, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('course_modules_id_seq', 200);

-- Lessons
INSERT INTO lessons (id, module_id, title, content, "order", duration_minutes, is_deleted, created_at, updated_at)
VALUES
  -- Module 100: Kirish
  (100, 100, 'Axborot xavfsizligi nima?', 'Axborot xavfsizligi — ma''lumotlarning maxfiyligi, yaxlitligi va foydalanuvchanligini ta''minlash jarayoni. Bu soha uch asosiy tamoyilga asoslanadi: Confidentiality (Maxfiylik), Integrity (Yaxlitlik), Availability (Foydalanuvchanlik) — CIA triadasi deb ataladi.', 1, 15, false, now(), now()),
  (101, 100, 'Kiberxavfsizlik tarixi', 'Kiberxavfsizlik kompyuter tarmoqlari paydo bo''lishi bilan birga rivojlandi. 1970-yillarda birinchi viruslar, 1990-yillarda internet keng tarqalishi bilan yangi tahdidlar paydo bo''ldi.', 2, 20, false, now(), now()),
  (102, 100, 'Asosiy atamalar', 'Malware, Phishing, Ransomware, DDoS, Social Engineering, Zero-day, Exploit, Vulnerability, Patch, Encryption — bu atamalarni bilish har bir xodim uchun muhim.', 3, 15, false, now(), now()),
  -- Module 101: Tahdidlar
  (110, 101, 'Malware turlari', 'Virus, troyan, worm, spyware, adware, rootkit — har birining o''z xususiyatlari va tarqalish usullari mavjud.', 1, 25, false, now(), now()),
  (111, 101, 'Ijtimoiy muhandislik', 'Fishing, vishing, smishing, pretexting — odamlarni aldash orqali ma''lumot olish usullari.', 2, 20, false, now(), now()),
  (112, 101, 'Ichki tahdidlar', 'Xodimlarning beparvoligi yoki qasddan zararli harakatlari eng katta xavf manbayi hisoblanadi.', 3, 15, false, now(), now()),
  -- Module 102: Himoya
  (120, 102, 'Antivirus va firewall', 'Antivirus dasturlari va xavfsizlik devorlarini to''g''ri sozlash va yangilash muhim ahamiyatga ega.', 1, 20, false, now(), now()),
  (121, 102, 'Shifrlash asoslari', 'Simmetrik va asimmetrik shifrlash, hash funksiyalar, raqamli imzolar — ma''lumotlarni himoyalash usullari.', 2, 30, false, now(), now()),
  (122, 102, 'Parol siyosati', 'Kuchli parollar yaratish, parol menejerlari, ikki bosqichli autentifikatsiya — eng muhim himoya vositalari.', 3, 15, false, now(), now()),
  -- Module 110
  (130, 110, 'Tarmoq hujumlari', 'Man-in-the-middle, ARP spoofing, DNS hijacking — tarmoq sathidagi hujum turlari va ulardan himoyalanish.', 1, 25, false, now(), now()),
  (131, 110, 'Web hujumlari', 'SQL injection, XSS, CSRF — web ilovalariga qaratilgan hujumlar va oldini olish.', 2, 25, false, now(), now()),
  -- Module 111
  (140, 111, 'SIEM tizimlari', 'Security Information and Event Management — xavfsizlik hodisalarini markaziy monitoring qilish tizimi.', 1, 30, false, now(), now()),
  (141, 111, 'Log tahlili', 'Tizim loglari tahlili orqali shubhali faoliyatni aniqlash usullari.', 2, 25, false, now(), now()),
  -- Module 120
  (150, 120, 'O''zbekiston qonunchiligi', 'Shaxsiy ma''lumotlar to''g''risidagi qonun va boshqa normativ hujjatlar tahlili.', 1, 30, false, now(), now()),
  (151, 120, 'Xalqaro standartlar', 'GDPR, ISO 27001 va boshqa xalqaro standartlar haqida umumiy ma''lumot.', 2, 25, false, now(), now()),
  -- Module 121
  (160, 121, 'Ma''lumotlarni tasniflash', 'Ommaviy, ichki foydalanish, maxfiy, o''ta maxfiy — ma''lumotlarni darajalash tartibi.', 1, 20, false, now(), now()),
  (161, 121, 'Ma''lumotlarni yo''q qilish', 'Ma''lumotlarni xavfsiz yo''q qilish usullari va standartlari.', 2, 15, false, now(), now()),
  -- Module 130
  (170, 130, 'Raqamli dalillar nima?', 'Raqamli dalillar — kompyuter, telefon va boshqa raqamli qurilmalardan olingan ma''lumotlar.', 1, 20, false, now(), now()),
  (171, 130, 'Dalillarni saqlash qoidalari', 'Chain of custody — dalillarni to''g''ri saqlash va hujjatlashtirish tartibi.', 2, 25, false, now(), now()),
  -- Module 131
  (180, 131, 'Disk tahlili', 'O''chirilgan fayllarni tiklash, metadata tahlili va disk image yaratish.', 1, 30, false, now(), now()),
  (181, 131, 'Tarmoq trafigi tahlili', 'Wireshark va boshqa vositalar yordamida tarmoq trafigini tahlil qilish.', 2, 30, false, now(), now()),
  -- Module 132
  (190, 132, 'Ekspert xulosasi', 'Raqamli kriminalistik ekspertiza xulosasi yozish tartibi va shakli.', 1, 25, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('lessons_id_seq', 300);

-- ──── NEWS ────
INSERT INTO news (id, title, content, is_active, is_broadcast, views_count, author_id, is_deleted, created_at, updated_at)
VALUES
  (100, 'Ta''lim platformasi ishga tushirildi!', 'Hurmatli xodimlar! IIV Ta''lim Platformasi bugundan boshlab rasman ishga tushirildi. Platformada testlar, kurslar, yangiliklar va boshqa imkoniyatlar mavjud. Faol ishtirok eting va bilimingizni oshiring!', true, false, 0, 1, false, now() - interval '5 days', now()),
  (101, 'Kiberxavfsizlik bo''yicha yangi kurs', 'Yangi "Kiberxavfsizlik amaliyoti" kursi platformaga qo''shildi. Kurs intermediate darajada bo''lib, amaliy ko''nikmalarni o''z ichiga oladi. Ro''yxatdan o''ting!', true, false, 0, 1, false, now() - interval '3 days', now()),
  (102, 'Haftalik reyting e''lon qilindi', 'Bu haftaning eng faol xodimlari aniqlandi. Reytingda yuqori o''rin egallagan xodimlar maxsus sertifikat bilan taqdirlanadi.', true, false, 0, 1, false, now() - interval '2 days', now()),
  (103, 'Yangi testlar qo''shildi', 'Tarmoq xavfsizligi va shaxsiy ma''lumotlarni himoya qilish bo''yicha yangi testlar qo''shildi. Bilimingizni sinab ko''ring!', true, false, 0, 1, false, now() - interval '1 day', now()),
  (104, 'Texnik ishlar haqida', 'Shanba kuni soat 03:00 dan 05:00 gacha texnik ishlar olib boriladi. Bu vaqt oralig''ida platforma vaqtincha ishlamasligi mumkin.', true, false, 0, 1, false, now(), now()),
  (105, 'Raqamli kriminalistika kursi ochildi', 'Ilg''or daraja uchun "Raqamli kriminalistika" kursi ochildi. Kursga 50 dan ortiq ballga ega xodimlar qatnasha oladi.', true, false, 0, 1, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('news_id_seq', 200);

-- ──── CHALLENGES ────
INSERT INTO challenges (id, title, description, challenge_type, target_value, reward_points, start_date, end_date, is_active, is_deleted, created_at, updated_at)
VALUES
  (100, 'Haftalik test maraton', 'Bu hafta kamida 3 ta test topshiring va bonus ball oling!', 'tests_count', 3, 10, CURRENT_DATE, CURRENT_DATE + interval '7 days', true, false, now(), now()),
  (101, 'Kurs o''rganuvchi', '1 ta kursni to''liq tugatib, bilimingizni oshiring!', 'courses_complete', 1, 15, CURRENT_DATE, CURRENT_DATE + interval '14 days', true, false, now(), now()),
  (102, '5 kunlik streak', 'Ketma-ket 5 kun platformaga kiring va faol bo''ling!', 'streak_days', 5, 8, CURRENT_DATE, CURRENT_DATE + interval '10 days', true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('challenges_id_seq', 200);

-- ──── USER RATING for existing user ────
INSERT INTO user_ratings (id, user_id, total_points, weekly_points, monthly_points, tests_taken, tests_passed, courses_completed, current_rank, is_deleted, created_at, updated_at)
VALUES (100, 1, 0, 0, 0, 0, 0, 0, 1, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('user_ratings_id_seq', 200);

-- ──── USER LEVEL for existing user ────
INSERT INTO user_levels (id, user_id, level, level_name, experience, is_deleted, created_at, updated_at)
VALUES (100, 1, 1, 'Yangi xodim', 0, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('user_levels_id_seq', 200);

-- ──── USER STREAK for existing user ────
INSERT INTO user_streaks (id, user_id, current_streak, longest_streak, last_activity_date, is_deleted, created_at, updated_at)
VALUES (100, 1, 0, 0, CURRENT_DATE, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('user_streaks_id_seq', 200);

-- ──── SURVEYS ────
INSERT INTO surveys (id, title, description, is_anonymous, is_active, created_by, total_responses, is_deleted, created_at, updated_at)
VALUES
  (100, 'Platforma baholash so''rovnomasi', 'Ta''lim platformasi haqidagi fikringizni bildiring', true, true, 1, 0, false, now(), now()),
  (101, 'Kiberxavfsizlik bilimi', 'Xodimlarning kiberxavfsizlik bilim darajasini baholash', false, true, 1, 0, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('surveys_id_seq', 200);

INSERT INTO survey_questions (id, survey_id, text, question_type, options, is_required, "order", is_deleted, created_at, updated_at)
VALUES
  (100, 100, 'Platformani qanchalik qulay deb baholaysiz?', 'choice', '["Juda qulay", "Qulay", "O''rtacha", "Noqulay"]', true, 1, false, now(), now()),
  (101, 100, 'Qaysi bo''lim sizga eng foydali?', 'choice', '["Testlar", "Kurslar", "Kutubxona", "AI Yordamchi"]', true, 2, false, now(), now()),
  (102, 100, 'Takliflaringiz bormi?', 'text', NULL, false, 3, false, now(), now()),
  (110, 101, 'Fishing xatni taniy olasizmi?', 'choice', '["Ha, albatta", "Ko''pincha", "Ba''zan", "Yo''q"]', true, 1, false, now(), now()),
  (111, 101, 'Parolingiz qanchalik kuchli?', 'choice', '["Juda kuchli (16+ belgi)", "Kuchli (12+ belgi)", "O''rtacha (8+ belgi)", "Zaif"]', true, 2, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('survey_questions_id_seq', 200);

-- ──── TASKS ────
INSERT INTO tasks (id, title, description, created_by, priority, status, deadline, is_active, is_deleted, created_at, updated_at)
VALUES
  (100, 'Kiberxavfsizlik testini topshirish', 'Barcha xodimlar "Kiberxavfsizlik asoslari" testini topshirishlari shart.', 1, 'high', 'pending', now() + interval '7 days', true, false, now(), now()),
  (101, 'Axborot xavfsizligi kursini o''rganish', 'Axborot xavfsizligi asoslari kursini to''liq o''rganish va tugatish.', 1, 'medium', 'pending', now() + interval '30 days', true, false, now(), now()),
  (102, 'Parollarni yangilash', 'Barcha tizim parollarini yangilash va kuchli parol qo''yish.', 1, 'urgent', 'pending', now() + interval '3 days', true, false, now(), now())
ON CONFLICT DO NOTHING;

SELECT setval('tasks_id_seq', 200);

-- Update organization_id for existing user
UPDATE users SET organization_id = 101 WHERE id = 1 AND organization_id IS NULL;

COMMIT;
