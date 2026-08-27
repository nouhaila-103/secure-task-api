from fastapi import FastAPI
from fastapi.responses import JSONResponse

from repository import TaskRepository
from service import TaskService


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple CRUD API using PostgreSQL for managing tasks.",
)


repository = TaskRepository()
service = TaskService(repository)


@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Check API health")
def health():
    return {"status": "ok"}


@app.get(
    "/tasks",
    summary="List all tasks",
    description="Returns all tasks stored in the PostgreSQL database.",
)
def get_tasks():
    return service.get_all_tasks()


@app.get(
    "/tasks/{task_id}",
    summary="Get one task",
    description="Returns a single task by its ID.",
)
def get_task(task_id: int):
    task = service.get_task(task_id)

    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )

    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task in the PostgreSQL database.",
)
def create_task(body: dict):
    title = body.get("title")

    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required and cannot be empty"},
        )

    return service.create_task(title)


@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, body: dict):
    result = service.update_task(task_id, body)

    if result is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )

    if "error" in result:
        return JSONResponse(
            status_code=400,
            content={"error": result["error"]},
        )

    return result


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
)
def delete_task(task_id: int):
    deleted = service.delete_task(task_id)

    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )

    return None