import { Course, TestItem, LeaderboardUser, Certificate, BadgeItem, UserProfile } from "@/types";

export const currentUserMock: UserProfile = {
  id: 1,
  telegramId: 87654321,
  fullName: "Alisher Rustamov",
  username: "alisher_rustamov",
  phone: "+998 90 123 45 67",
  role: "officer",
  organization: "IIV Akademiyasi",
  position: "Katta inspektor",
  rank: "Mayor",
  avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
  streakDays: 12,
  points: 1450,
  completedCoursesCount: 4,
  certificatesCount: 3,
  isBanned: false,
};

export const coursesMock: Course[] = [
  {
    id: "course-1",
    title: "Kiberxavfsizlik va axborot himoyasi asoslari",
    category: "Axborot texnologiyalari",
    description: "Huquqni muhofaza qilish organlarida zamonaviy kiberxavfsizlik tahdidlari, fishing, feyk xabarlar va ma'lumotlar bazasini himoyalash qoidalari.",
    coverImage: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80",
    instructor: "Polkovnik D. Xolmatov",
    durationHours: 18,
    lessonsCount: 8,
    studentsCount: 342,
    rating: 4.9,
    reviewsCount: 89,
    status: "published",
    progressPercentage: 75,
    modules: [
      {
        id: "m-1",
        title: "1-Modul: Kiberxavfsizlikka kirish",
        order: 1,
        lessons: [
          {
            id: "l-1",
            title: "Zamonaviy raqamli tahdidlar turlari",
            order: 1,
            durationMinutes: 15,
            content: `Ushbu darsda biz kiberjinoyatchilikning asosiy usullarini o'rganamiz:

1. **Fishing (Phishing)** — soxta havolalar va elektron pochta xabarlari orqali shaxsiy ma'lumotlarni o'g'irlash.
2. **Social Engineering** — inson omilidan foydalanib tizim parollarini qo'lga kiritish.
3. **Zararli dasturlar (Malware)** — troyan, ransomware va spyware vositalari.

Davlat va huquqni muhofaza qiluvchi organ xodimlari o'z shaxsiy va xizmat qurilmalarida ikki bosqichli autentifikatsiya (2FA) dan foydalanishi majburiydir.`,
            videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
            attachments: [
              { id: "att-1", title: "Kiberxavfsizlik qo'llanmasi (PDF)", type: "pdf", url: "#", size: "3.2 MB" },
              { id: "att-2", title: "Parol xavfsizligi infografikasi", type: "pdf", url: "#", size: "1.1 MB" }
            ],
            isCompleted: true,
          },
          {
            id: "l-2",
            title: "Ijtimoiy muhandislikdan himoyalanish",
            order: 2,
            durationMinutes: 20,
            content: `Ijtimoiy muhandislik hujumlariga qarshi asosiy profilaktika choralari:
- Xizmat sirlarini begonalarga oshkor qilmaslik;
- Telegram bot va guruhlarda shubhali fayllarni ochmaslik;
- Tezkor hisobot berish protokoli.`,
            isCompleted: true,
          }
        ]
      },
      {
        id: "m-2",
        title: "2-Modul: Tizim xavfsizligi va shifrlash",
        order: 2,
        lessons: [
          {
            id: "l-3",
            title: "Kriptografiya va xizmat ma'lumotlarini shifrlash",
            order: 1,
            durationMinutes: 25,
            content: `Ma'lumotlar bazalarini shifrlashda AES-256 va RSA algoritmlari qo'llanilishi:
- Shaxsiy ma'lumotlarni qayta ishlash qonunchiligi;
- Elektron raqamli imzo (ERI) sertifikatlari bilan ishlash.`,
            isCompleted: false,
          }
        ]
      }
    ]
  },
  {
    id: "course-2",
    title: "Yo'l harakati xavfsizligini ta'minlash va yangi qoidalar",
    category: "Yo'l harakati",
    description: "Yangi tahrirdagi Yo'l harakati qoidalari, radar tizimlari, YTH holatlarini rasmiylashtirish va haydovchilar bilan muloqot madaniyati.",
    coverImage: "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=800&q=80",
    instructor: "Mayor Sh. Qodirov",
    durationHours: 24,
    lessonsCount: 12,
    studentsCount: 620,
    rating: 4.8,
    reviewsCount: 145,
    status: "published",
    progressPercentage: 40,
    modules: [
      {
        id: "m-3",
        title: "1-Modul: Yangi YHQ standartlari",
        order: 1,
        lessons: [
          {
            id: "l-4",
            title: "Tezlik me'yorlari va elektron nazorat",
            order: 1,
            durationMinutes: 18,
            content: "Aholi punktlarida 60 km/soat tezlik me'yori va uning qo'llanish amaliyoti.",
            isCompleted: true,
          }
        ]
      }
    ]
  },
  {
    id: "course-3",
    title: "Kriminalistika va dalillarni yig'ish metodikasi",
    category: "Tergov va Kriminalistika",
    description: "Hodisa sodir bo'lgan joyni ko'zdan kechirish, daktiloskopik izlar, biologik va raqamli ashyoviy dalillarni to'g'ri qayd etish usullari.",
    coverImage: "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80",
    instructor: "Podpolkovnik A. Saidov",
    durationHours: 32,
    lessonsCount: 16,
    studentsCount: 280,
    rating: 5.0,
    reviewsCount: 78,
    status: "published",
    progressPercentage: 0,
    modules: []
  },
  {
    id: "course-4",
    title: "Huquqiy savodxonlik va inson huquqlari standartlari",
    category: "Huquqshunoslik",
    description: "Fuqarolar bilan muloqotda inson qadr-qimmati, xizmat burchi va xalqaro konvensiya talablari.",
    coverImage: "https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=800&q=80",
    instructor: "Dotsent N. Yusupova",
    durationHours: 14,
    lessonsCount: 7,
    studentsCount: 510,
    rating: 4.7,
    reviewsCount: 112,
    status: "published",
    progressPercentage: 100,
    modules: []
  }
];

export const testsMock: TestItem[] = [
  {
    id: "test-1",
    courseId: "course-1",
    courseTitle: "Kiberxavfsizlik va axborot himoyasi asoslari",
    title: "Kiberxavfsizlik: 1-Modul bo'yicha oraliq nazorat",
    description: "Fishing, parollar xavfsizligi va 2FA bo'yicha bilimlarni tekshirish.",
    durationMinutes: 15,
    passPercentage: 70,
    questionsCount: 5,
    totalAttemptsAllowed: 3,
    userBestScore: 85,
    questions: [
      {
        id: "q-1",
        text: "Ikki bosqichli autentifikatsiya (2FA) nima uchun zarur?",
        points: 20,
        options: [
          { id: "opt-1", text: "Faqat tizimga kirish tezligini oshirish uchun", isCorrect: false },
          { id: "opt-2", text: "Parol o'g'irlangan taqdirda ham hisobni qo'shimcha tasdiq kodi bilan himoyalash uchun", isCorrect: true },
          { id: "opt-3", text: "Internet tezligini tejash uchun", isCorrect: false },
          { id: "opt-4", text: "Brauzer tarixini tozalash uchun", isCorrect: false }
        ]
      },
      {
        id: "q-2",
        text: "Fishing (Phishing) hujumining asosiy belgisi nima?",
        points: 20,
        options: [
          { id: "opt-5", text: "Kutilmagan manbadan kelgan, shoshiltiruvchi va soxta havolaga ega xabar", isCorrect: true },
          { id: "opt-6", text: "Kompyuter ekranining yorug'ligi pasayishi", isCorrect: false },
          { id: "opt-7", text: "Antivirus dasturining avtomatik yangilanishi", isCorrect: false },
          { id: "opt-8", text: "Wi-Fi parolini o'zgartirish talabi", isCorrect: false }
        ]
      },
      {
        id: "q-3",
        text: "Xizmat kompyuterida qanday paroldan foydalanish tavsiya etiladi?",
        points: 20,
        options: [
          { id: "opt-9", text: "Kamida 12 ta belgi: katta-kichik harf, raqam va maxsus belgilardan iborat murakkab parol", isCorrect: true },
          { id: "opt-10", text: "Tug'ilgan sana va ism kombinatsiyasi", isCorrect: false },
          { id: "opt-11", text: "Ketma-ket keluvchi 12345678 raqamlari", isCorrect: false },
          { id: "opt-12", text: "Monitor tagiga qog'ozda yopishtirilgan qisqa so'z", isCorrect: false }
        ]
      },
      {
        id: "q-4",
        text: "Telegram ilovasida xizmat sirlarini himoyalash uchun eng birinchi qilinadigan amal:",
        points: 20,
        options: [
          { id: "opt-13", text: "Bulutli parol (Two-Step Verification) o'rnatish va faol seanslarni tekshirish", isCorrect: true },
          { id: "opt-14", text: "Yangi stiker to'plamini o'rnatish", isCorrect: false },
          { id: "opt-15", text: "Foydalanuvchi ismini o'zgartirish", isCorrect: false },
          { id: "opt-16", text: "Barcha xabarlarni saqlab qo'yish", isCorrect: false }
        ]
      },
      {
        id: "q-5",
        text: "Zararli ilova (Trojan) qurilmaga tushganda nima sodir bo'lishi mumkin?",
        points: 20,
        options: [
          { id: "opt-17", text: "Foydalanuvchining klaviaturada tergan ma'lumotlari va parollari begona serverga uzatiladi", isCorrect: true },
          { id: "opt-18", text: "Qurilmaning batareyasi doim 100% bo'lib qoladi", isCorrect: false },
          { id: "opt-19", text: "Ekranda yangi o'yinlar avtomatik yuklanadi", isCorrect: false },
          { id: "opt-20", text: "Faqat ovoz balandligi pasayadi", isCorrect: false }
        ]
      }
    ]
  },
  {
    id: "test-2",
    courseId: "course-2",
    courseTitle: "Yo'l harakati xavfsizligini ta'minlash",
    title: "YHQ bo'yicha attestatsiya testi",
    description: "Yo'l belgilari, chorrahalarni kesib o'tish va maxsus transport vositalari.",
    durationMinutes: 20,
    passPercentage: 80,
    questionsCount: 10,
    totalAttemptsAllowed: 2,
    questions: []
  }
];

export const leaderboardMock: LeaderboardUser[] = [
  { rank: 1, id: 101, fullName: "Javohir Toshmatov", organization: "Tergov boshqarmasi", points: 2840, streakDays: 28, badge: "Master", avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80" },
  { rank: 2, id: 102, fullName: "Nilufar Karimova", organization: "IIV Akademiyasi", points: 2610, streakDays: 24, badge: "Ekspert", avatarUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80" },
  { rank: 3, id: 103, fullName: "Botir Ergashev", organization: "YHX boshqarmasi", points: 2350, streakDays: 19, badge: "Top 3", avatarUrl: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80" },
  { rank: 4, id: 1, fullName: "Alisher Rustamov (Siz)", organization: "IIV Akademiyasi", points: 1450, streakDays: 12, badge: "Faol", avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" },
  { rank: 5, id: 105, fullName: "Sardor Umarov", organization: "Kriminalistika markazi", points: 1390, streakDays: 11, badge: "Izlanuvchi" },
  { rank: 6, id: 106, fullName: "Madina Qosimova", organization: "Huquqbuzarliklar profilaktikasi", points: 1280, streakDays: 9, badge: "Izlanuvchi" }
];

export const certificatesMock: Certificate[] = [
  {
    id: "cert-001",
    certificateNumber: "IIV-EDU-2026-0891",
    courseId: "course-4",
    courseTitle: "Huquqiy savodxonlik va inson huquqlari standartlari",
    issueDate: "15-May, 2026",
    studentName: "Alisher Rustamov",
    organization: "IIV Akademiyasi",
    scorePercentage: 94,
    qrCodeUrl: "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://edubot.iiv.uz/verify/IIV-EDU-2026-0891"
  },
  {
    id: "cert-002",
    certificateNumber: "IIV-EDU-2026-0412",
    courseId: "course-1",
    courseTitle: "Axborot xavfsizligi boshlang'ich kursi",
    issueDate: "02-Aprel, 2026",
    studentName: "Alisher Rustamov",
    organization: "IIV Akademiyasi",
    scorePercentage: 88,
    qrCodeUrl: "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://edubot.iiv.uz/verify/IIV-EDU-2026-0412"
  }
];

export const badgesMock: BadgeItem[] = [
  { id: "b-1", name: "Kiber Qalqon", description: "Axborot xavfsizligi bo'yicha 1-o'rin", icon: "🛡️", isUnlocked: true, unlockedAt: "10-May, 2026" },
  { id: "b-2", name: "10 Kunlik Streak", description: "Ketma-ket 10 kun darslarni o'zlashtirish", icon: "🔥", isUnlocked: true, unlockedAt: "12-May, 2026" },
  { id: "b-3", name: "A'lochi Testchi", description: "Barcha testlarni 90%+ ball bilan topshirish", icon: "⭐", isUnlocked: true, unlockedAt: "15-May, 2026" },
  { id: "b-4", name: "Akademiya Lideri", description: "Haftalik reytingda top 5 talikka kirish", icon: "🏆", isUnlocked: false },
  { id: "b-5", name: "Tezkor Yechuvchi", description: "Testni vaqtning yarmidan tez yakunlash", icon: "⚡", isUnlocked: false }
];
