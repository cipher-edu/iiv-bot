from bot.config import settings


SCORE_MAP = {
    "excellent": settings.score_excellent,
    "good": settings.score_good,
    "satisfactory": settings.score_satisfactory,
    "participation": settings.score_participation,
    "course_complete": settings.score_course_complete,
    "streak_bonus": settings.score_streak_bonus,
    "challenge_bonus": settings.score_challenge_bonus,
}

THRESHOLD_MAP = {
    "excellent": settings.score_excellent_threshold,
    "good": settings.score_good_threshold,
    "satisfactory": settings.score_satisfactory_threshold,
}

MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
MAX_CALLBACK_DATA_LENGTH = 64

PAGINATION_BUTTONS_ROW = 5

LEVELS = [
    {"name": "Yangi xodim", "min_points": 0, "max_points": 49},
    {"name": "Faol xodim", "min_points": 50, "max_points": 149},
    {"name": "Tajribali", "min_points": 150, "max_points": 349},
    {"name": "Mutaxassis", "min_points": 350, "max_points": 699},
    {"name": "Ekspert", "min_points": 700, "max_points": 1499},
    {"name": "Master", "min_points": 1500, "max_points": float("inf")},
]

STREAK_MILESTONES = [7, 14, 30, 60, 100, 365]

BADGE_LABELS = {
    "first_test": "Birinchi test",
    "ten_tests": "10 ta test",
    "perfect_score": "Mukammal natija",
    "first_course": "Birinchi kurs",
    "five_courses": "5 ta kurs",
    "streak_7": "7 kunlik streak",
    "streak_30": "30 kunlik streak",
    "top_weekly": "Hafta yulduzi",
    "helper": "Yordamchi",
    "early_bird": "Erta qush",
}

MENU_TEXTS = {
    "main_menu": "Asosiy menyu",
    "tests": "Testlar",
    "courses": "Kurslar",
    "news": "Yangiliklar",
    "rating": "Reyting",
    "certificates": "Sertifikatlar",
    "profile": "Profil",
    "library": "Kutubxona",
    "achievements": "Yutuqlar",
    "ai_chat": "AI Yordamchi",
    "help": "Yordam",
    "admin_panel": "Admin panel",
}
