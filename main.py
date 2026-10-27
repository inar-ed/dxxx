import sqlite3

from db import init_db, fill_test_data
from queries import (
    q1_free_seats,
    q2_teacher_schedule,
    q3_attendance_percent,
    q4_students_multi_group,
)


def demo_constraints(conn):
    print("\n=== ПРОВЕРКА ОГРАНИЧЕНИЙ (все плохие вставки должны быть отклонены) ===")

    def attempt(label, sql, params=()):
        try:
            with conn:
                conn.execute(sql, params)
            print(f"  [ПРОПУЩЕНО ✗] {label}")
        except sqlite3.IntegrityError as e:
            print(f"  [OK, отклонено] {label}: {e}")

    attempt(
        "запись в переполненную группу 1",
        "insert into enrollments values (100, 5, 1, '2024-09-05', 'active')",
    )
    attempt(
        "повторная активная запись студента 1 в группу 1",
        "insert into enrollments values (101, 1, 1, '2024-09-05', 'active')",
    )
    attempt(
        "в enrollments вписан преподаватель (id=6, не студент)",
        "insert into enrollments values (102, 6, 4, '2024-09-05', 'active')",
    )
    attempt(
        "пересечение по аудитории 101",
        "insert into lessons values (101, 1, 6, '2024-09-16', '11:00', '12:00', 'X', '101')",
    )
    attempt(
        "пересечение у преподавателя 7",
        "insert into lessons values (102, 2, 7, '2024-09-16', '14:30', '16:00', 'X', '105')",
    )
    attempt(
        "в качестве ведущего указан студент (id=1)",
        "insert into lessons values (103, 1, 1, '2024-09-25', '10:00', '11:30', 'X', '101')",
    )
    attempt(
        "посещаемость: запись группы 1, а занятие группы 2",
        "insert into attendance values (1, 4, 1)",
    )


def main():
    conn = init_db()
    fill_test_data(conn)

    print("=" * 78)
    print("ТЕМА 2. УЧЕБНЫЙ ЦЕНТР И ЗАПИСЬ НА КУРСЫ  (6 таблиц)")
    print("=" * 78)

    print("\n[1] Группы курса 'Python-разработка' (id=1) со свободными местами:")
    print(f"  {'ID':>3}  {'Группа':<10} {'Начало':<12} {'Конец':<12} "
          f"{'Мест':>4} {'Занято':>6} {'Свободно':>8}")
    for r in q1_free_seats(conn, 1):
        print(f"  {r[0]:>3}  {r[1]:<10} {r[2]:<12} {r[3]:<12} "
              f"{r[4]:>4} {r[5]:>6} {r[6]:>8}")

    print("\n[2] Расписание преподавателя 7 на неделю 16.09–22.09.2024:")
    print(f"  {'Дата':<12} {'Время':<13} {'Ауд':<5} {'Курс':<22} {'Группа':<12} Тема")
    for r in q2_teacher_schedule(conn, 7, "2024-09-16", "2024-09-22"):
        print(f"  {r[0]:<12} {r[1]}-{r[2]:<8} {r[3]:<5} {r[5]:<22} {r[6]:<12} {r[4]}")

    print("\n[3] Посещаемость группы 1 за сентябрь 2024:")
    print(f"  {'Студент':<22} {'Всего':>6} {'Посетил':>8} {'%':>7}")
    for r in q3_attendance_percent(conn, 1, "2024-09-01", "2024-09-30"):
        print(f"  {r[0]:<22} {r[1]:>6} {r[2]:>8} {r[3]:>7}")

    print("\n[4] Студенты, активно записанные более чем в одну группу:")
    print(f"  {'ID':>3}  {'Студент':<22} {'Активных групп':>15}")
    for r in q4_students_multi_group(conn):
        print(f"  {r[0]:>3}  {r[1]:<22} {r[2]:>15}")

    demo_constraints(conn)
    conn.close()


if __name__ == "__main__":
    main()