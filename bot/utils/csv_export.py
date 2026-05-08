import csv
import io
from typing import Sequence, Any


def generate_csv(headers: list[str], rows: Sequence[Sequence[Any]]) -> io.BytesIO:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    buffer = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    buffer.seek(0)
    return buffer


def users_to_csv(users) -> io.BytesIO:
    headers = ["ID", "Telegram ID", "F.I.O.", "Telefon", "Rol", "Status", "Ro'yxatdan o'tgan"]
    rows = [
        [
            u.id,
            u.telegram_id,
            u.full_name or "",
            u.phone or "",
            u.role,
            u.status,
            u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
        ]
        for u in users
    ]
    return generate_csv(headers, rows)


def test_results_to_csv(results) -> io.BytesIO:
    headers = ["ID", "Foydalanuvchi ID", "Test ID", "Ball", "To'g'ri javoblar", "Jami savollar", "Sana"]
    rows = [
        [
            r.id,
            r.user_id,
            r.test_id,
            r.score,
            r.correct_answers,
            r.total_questions,
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        ]
        for r in results
    ]
    return generate_csv(headers, rows)


def ratings_to_csv(ratings) -> io.BytesIO:
    headers = ["ID", "Foydalanuvchi ID", "Jami ball", "Haftalik", "Oylik"]
    rows = [
        [r.id, r.user_id, r.total_points, r.weekly_points, r.monthly_points]
        for r in ratings
    ]
    return generate_csv(headers, rows)
