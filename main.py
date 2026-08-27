from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from repository import TaskRepository
from service import TaskService
from supabase_client import supabase


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple CRUD API using PostgreSQL and Supabase Auth.",
)


class AuthRequest(BaseModel):
    email: str
    password: str


repository = TaskRepository()
service = TaskService(repository)


# --------------------------------------------------
# General routes
# --------------------------------------------------

@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/tasks",
            "/auth/signup",
            "/auth/login",
            "/public/info",
            "/protected/profile",
        ],
    }


@app.get("/health", summary="Check API health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# Task routes
# --------------------------------------------------

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


# --------------------------------------------------
# Authentication
# --------------------------------------------------

@app.post(
    "/auth/signup",
    status_code=201,
    summary="Create a new user",
)
def signup(data: AuthRequest):
    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required",
        )

    try:
        response = supabase.auth.sign_up(
            {
                "email": data.email,
                "password": data.password,
            }
        )

        return {
            "user": response.user.model_dump() if response.user else None
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to create account",
        )


@app.post(
    "/auth/login",
    summary="Log in",
)
def login(data: AuthRequest):
    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required",
        )

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": data.email,
                "password": data.password,
            }
        )

        if not response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid login credentials",
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials",
        )


# --------------------------------------------------
# Stage 2: Public route
# --------------------------------------------------

@app.get(
    "/public/info",
    summary="Public information",
)
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


# --------------------------------------------------
# Stage 3: Protected profile
# --------------------------------------------------

@app.get(
    "/protected/profile",
    summary="Get authenticated user profile",
)
def protected_profile(
    authorization: str | None = Header(default=None)
):
    # Check that Authorization header exists
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    # Check Bearer format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    # Extract token
    token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    # Verify token with Supabase
    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
            )

        user = response.user

        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )