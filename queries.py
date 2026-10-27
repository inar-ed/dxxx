def q1_free_seats(conn, course_id):
    sql = """
    select g.id, g.name, g.start_date, g.end_date,
           g.capacity,
           count(e.id)              as active_count,
           g.capacity - count(e.id) as free_seats
    from groups g
    left join enrollments e
           on e.group_id = g.id and e.status = 'active'
    where g.course_id = ?
    group by g.id
    having g.capacity - count(e.id) > 0
    order by g.name
    """
    return conn.execute(sql, (course_id,)).fetchall()


def q2_teacher_schedule(conn, teacher_id, date_from, date_to):
    sql = """
    select l.lesson_date, l.start_time, l.end_time, l.room, l.topic,
           c.title, g.name
    from lessons l
    join groups  g on g.id = l.group_id
    join courses c on c.id = g.course_id
    where l.teacher_id = ?
      and l.lesson_date between ? and ?
    order by l.lesson_date, l.start_time
    """
    return conn.execute(sql, (teacher_id, date_from, date_to)).fetchall()


def q3_attendance_percent(conn, group_id, date_from, date_to):
    sql = """
    select p.full_name,
           count(l.id)                              as total_lessons,
           coalesce(sum(a.present), 0)              as attended,
           round(100.0 * coalesce(sum(a.present), 0)
                 / count(l.id), 2)                  as percent
    from enrollments e
    join people  p on p.id = e.student_id
    join lessons l on l.group_id = e.group_id
    left join attendance a
           on a.enrollment_id = e.id and a.lesson_id = l.id
    where e.group_id = ?
      and e.status in ('active', 'completed')
      and l.lesson_date between ? and ?
    group by e.id
    order by percent desc, p.full_name
    """
    return conn.execute(sql, (group_id, date_from, date_to)).fetchall()


def q4_students_multi_group(conn):
    sql = """
    select p.id, p.full_name, count(e.group_id) as active_groups
    from people p
    join enrollments e on e.student_id = p.id and e.status = 'active'
    where p.is_student = 1
    group by p.id
    having count(e.group_id) > 1
    order by active_groups desc, p.full_name
    """
    return conn.execute(sql).fetchall()