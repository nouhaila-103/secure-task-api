class TaskService:
    def __init__(self, repository):
        self.repository = repository

    def get_all_tasks(self):
        return self.repository.get_all()

    def get_task(self, task_id):
        return self.repository.get_by_id(task_id)

    def create_task(self, title):
        if not isinstance(title, str) or not title.strip():
            return None

        return self.repository.create(title.strip())

    def update_task(self, task_id, body):
        if not body:
            return {"error": "Request body cannot be empty"}

        task = self.repository.get_by_id(task_id)

        if task is None:
            return None

        current_title = task["title"]
        current_done = task["done"]

        if "title" in body:
            if (
                not isinstance(body["title"], str)
                or not body["title"].strip()
            ):
                return {"error": "Title cannot be empty"}

            current_title = body["title"].strip()

        if "done" in body:
            if not isinstance(body["done"], bool):
                return {"error": "Done must be true or false"}

            current_done = body["done"]

        return self.repository.update(
            task_id,
            current_title,
            current_done,
        )

    def delete_task(self, task_id):
        return self.repository.delete(task_id)