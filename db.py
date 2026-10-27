import sqlite3

DB_PATH = ":memory:"

DDL = """
create table people (
    id         integer primary key,
    full_name  text    not null,
    phone      text    not null unique,
    email      text    unique,
    is_student integer not null default 0 check (is_student in (0,1)),
    is_teacher integer not null default 0 check (is_teacher in (0,1)),
    check (is_student = 1 or is_teacher = 1)
);

create table courses (
    id          integer primary key,
    title       text    not null unique,
    description text
);

create table groups (
    id         integer primary key,
    course_id  integer not null references courses(id),
    name       text    not null,
    start_date text    not null,
    end_date   text    not null,
    capacity   integer not null check (capacity > 0),
    check (start_date <= end_date),
    unique (course_id, name)
);

create table enrollments (
    id          integer primary key,
    student_id  integer not null references people(id),
    group_id    integer not null references groups(id),
    enrolled_at text    not null,
    status      text    not null check (status in ('active','completed','cancelled'))
);

create unique index ux_active_enrollment
    on enrollments (student_id, group_id)
    where status = 'active';

create table lessons (
    id          integer primary key,
    group_id    integer not null references groups(id) on delete cascade,
    teacher_id  integer not null references people(id),
    lesson_date text    not null,
    start_time  text    not null,
    end_time    text    not null,
    topic       text,
    room        text    not null,
    check (start_time < end_time)
);

create table attendance (
    enrollment_id integer not null references enrollments(id) on delete cascade,
    lesson_id     integer not null references lessons(id)     on delete cascade,
    present       integer not null check (present in (0,1)),
    primary key (enrollment_id, lesson_id)
);

create trigger trg_enroll_must_be_student
before insert on enrollments
for each row
when (select is_student from people where id = new.student_id) <> 1
begin
    select raise(abort, 'Записываемый должен иметь роль студента');
end;

create trigger trg_lesson_must_be_teacher
before insert on lessons
for each row
when (select is_teacher from people where id = new.teacher_id) <> 1
begin
    select raise(abort, 'Ведущий занятия должен иметь роль преподавателя');
end;

create trigger trg_lesson_room_busy
before insert on lessons
for each row
when exists (
    select 1 from lessons l
    where l.room = new.room
      and l.lesson_date = new.lesson_date
      and new.start_time < l.end_time
      and l.start_time < new.end_time
)
begin
    select raise(abort, 'Аудитория занята в это время');
end;

create trigger trg_lesson_teacher_busy
before insert on lessons
for each row
when exists (
    select 1 from lessons l
    where l.teacher_id = new.teacher_id
      and l.lesson_date = new.lesson_date
      and new.start_time < l.end_time
      and l.start_time < new.end_time
)
begin
    select raise(abort, 'У преподавателя уже есть занятие в это время');
end;

create trigger trg_enrollment_capacity
before insert on enrollments
for each row
when new.status = 'active'
 and (select count(*) from enrollments e
      where e.group_id = new.group_id and e.status = 'active')
     >= (select capacity from groups where id = new.group_id)
begin
    select raise(abort, 'В группе нет свободных мест');
end;

create trigger trg_attendance_group_match
before insert on attendance
for each row
when (select group_id from enrollments where id = new.enrollment_id)
   <> (select group_id from lessons     where id = new.lesson_id)
begin
    select raise(abort, 'Занятие не относится к группе записи');
end;
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("pragma foreign_keys = on")
    conn.executescript(DDL)
    return conn


def fill_test_data(conn):
    people = [
        (1, "Алексеев Алексей",       "+79110000001", "alekseev@mail.ru",  1, 0),
        (2, "Борисова Бэла",          "+79110000002", "borisova@mail.ru",  1, 0),
        (3, "Волков Виктор",          "+79110000003", "volkov@mail.ru",    1, 0),
        (4, "Громова Галина",         "+79110000004", "gromova@mail.ru",   1, 0),
        (5, "Дмитриев Дмитрий",       "+79110000005", "dmitriev@mail.ru",  1, 0),
        (6, "Иванов Иван Иванович",   "+79000000001", "ivanov@edu.ru",     0, 1),
        (7, "Петрова Анна Сергеевна", "+79000000002", "petrova@edu.ru",    0, 1),
        (8, "Сидоров Пётр Петрович",  "+79000000003", "sidorov@edu.ru",    0, 1),
    ]
    courses = [
        (1, "Python-разработка",  "Базовый курс по Python"),
        (2, "Графический дизайн", "Композиция, цвет, вёрстка"),
        (3, "Английский язык A1", "Начальный уровень"),
    ]
    groups = [
        (1, 1, "Python-A",   "2024-09-02", "2024-12-20", 3),
        (2, 1, "Python-B",   "2024-09-02", "2024-12-20", 2),
        (3, 2, "Design-A",   "2024-10-01", "2025-01-31", 5),
        (4, 3, "English-A1", "2024-09-15", "2024-12-15", 4),
    ]
    enrollments = [
        (1,  1, 1, "2024-08-20", "active"),
        (2,  2, 1, "2024-08-20", "active"),
        (3,  3, 1, "2024-08-21", "active"),
        (4,  1, 2, "2024-08-22", "active"),
        (5,  4, 2, "2024-08-23", "cancelled"),
        (6,  1, 3, "2024-09-10", "active"),
        (7,  2, 3, "2024-09-10", "active"),
        (8,  5, 3, "2024-09-11", "active"),
        (9,  3, 4, "2024-09-01", "active"),
        (10, 4, 4, "2024-09-02", "active"),
        (11, 5, 4, "2024-09-03", "completed"),
    ]
    lessons = [
        (1, 1, 6, "2024-09-16", "10:00", "11:30", "Введение",       "101"),
        (2, 1, 6, "2024-09-18", "10:00", "11:30", "Типы данных",    "101"),
        (3, 1, 6, "2024-09-20", "10:00", "11:30", "Условия",        "101"),
        (4, 2, 7, "2024-09-17", "12:00", "13:30", "Введение",       "102"),
        (5, 2, 7, "2024-09-19", "12:00", "13:30", "Функции",        "102"),
        (6, 3, 7, "2024-09-16", "14:00", "15:30", "Композиция",     "103"),
        (7, 3, 8, "2024-09-18", "14:00", "15:30", "Цвет",           "103"),
        (8, 4, 8, "2024-09-17", "09:00", "10:30", "Present Simple", "104"),
    ]
    attendance = [
        (1, 1, 1), (1, 2, 1), (1, 3, 1),
        (2, 1, 1), (2, 2, 1), (2, 3, 0),
        (3, 1, 0), (3, 2, 0), (3, 3, 0),
        (4, 4, 1), (4, 5, 0),
        (6, 6, 1), (6, 7, 1),
        (7, 6, 0), (7, 7, 1),
        (9, 8, 1), (10, 8, 1),
    ]

    with conn:
        conn.executemany("insert into people      values (?,?,?,?,?,?)", people)
        conn.executemany("insert into courses     values (?,?,?)",       courses)
        conn.executemany("insert into groups      values (?,?,?,?,?,?)", groups)
        conn.executemany("insert into enrollments values (?,?,?,?,?)",   enrollments)
        conn.executemany("insert into lessons     values (?,?,?,?,?,?,?,?)", lessons)
        conn.executemany("insert into attendance  values (?,?,?)",       attendance)