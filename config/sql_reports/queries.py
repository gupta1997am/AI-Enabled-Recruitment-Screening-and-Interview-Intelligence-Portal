# recruitment/sql_reports/queries.py

from django.db import connection


def execute_query(sql, params=None):
    """Execute a parameterized SQL query and return rows as dictionaries."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [column[0] for column in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def get_candidate_status_summary():
    """Count candidates by their historical selection status."""
    sql = """
        SELECT
            historical_selection_status AS status,
            COUNT(*) AS total
        FROM recruitment_candidate
        GROUP BY historical_selection_status
        ORDER BY total DESC
    """
    return execute_query(sql)


def get_candidates_by_role(role_name):
    """Find candidates whose applied role matches the supplied role."""
    sql = """
        SELECT
            id,
            candidate_name,
            email,
            applied_role,
            experience_months,
            historical_selection_status
        FROM recruitment_candidate
        WHERE LOWER(applied_role) = LOWER(%s)
        ORDER BY candidate_name
    """
    return execute_query(sql, [role_name])


def get_screening_summary_by_role():
    """Count screening results by job role and screening status."""
    sql = """
        SELECT
            job_role.title AS role_title,
            screening.status AS screening_status,
            COUNT(*) AS total
        FROM recruitment_screeningresult AS screening
        INNER JOIN recruitment_jobrole AS job_role
            ON screening.role_id = job_role.id
        GROUP BY job_role.title, screening.status
        ORDER BY job_role.title, screening.status
    """
    return execute_query(sql)


def get_candidate_count():
    """Return the total number of candidates."""
    sql = "SELECT COUNT(*) AS total FROM recruitment_candidate"
    rows = execute_query(sql)
    return rows[0]["total"] if rows else 0