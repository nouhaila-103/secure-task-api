import os
import psycopg


class TaskRepository:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

    def get_all(self):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, done
                    FROM tasks
                    ORDER BY id
                    """
                )

                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "done": row[2],
            }
            for row in rows
        ]

    def get_by_id(self, task_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, done
                    FROM tasks
                    WHERE id = %s
                    """,
                    (task_id,),
                )

                row = cur.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }

    def create(self, title):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (title, done)
                    VALUES (%s, %s)
                    RETURNING id, title, done
                    """,
                    (title, False),
                )

                row = cur.fetchone()

            conn.commit()

        return {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }

    def update(self, task_id, title, done):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tasks
                    SET title = %s, done = %s
                    WHERE id = %s
                    RETURNING id, title, done
                    """,
                    (title, done, task_id),
                )

                row = cur.fetchone()

            conn.commit()

        if row is None:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }

    def delete(self, task_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = %s
                    RETURNING id
                    """,
                    (task_id,),
                )

                row = cur.fetchone()

            conn.commit()

        return row is not None