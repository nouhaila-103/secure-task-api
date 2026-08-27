from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from repository import TaskRepository
from service import TaskService
from supabase_client import supabase


app = FastAPI(
    title="Task API",
    version="1.0",
    description="Task CRUD API with Supabase authentication.",
)


# ============================================================
# AUTH
# ============================================================

class AuthRequest(BaseModel):
    email: str
    password: str


# This creates the "Authorize" button in Swagger
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Reusable authentication dependency.

    Checks the Authorization header:
    Authorization: Bearer <token>

    Then asks Supabase to verify the token.
    """

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
        )

    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ============================================================
# DATABASE / SERVICES
# ============================================================

repository = TaskRepository()
service = TaskService(repository)


# ============================================================
# GENERAL ROUTES
# ============================================================

@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/tasks",
            "/auth/signup",
            "/auth/login",
            "/auth/logout",
            "/public/info",
            "/protected/profile",
            "/protected/dashboard",
            "/docs",
        ],
    }


@app.get("/health", summary="Check API health")
def health():
    return {"status": "ok"}


# ============================================================
# PUBLIC ROUTE
# ============================================================

@app.get(
    "/public/info",
    summary="Public information",
)
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


# ============================================================
# AUTH - SIGN UP
# ============================================================

@app.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def signup(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            "user": (
                response.user.model_dump()
                if response.user
                else None
            )
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create account",
        )


# ============================================================
# AUTH - LOGIN
# ============================================================

@app.post(
    "/auth/login",
    summary="Log in",
)
def login(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
                status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
        )


# ============================================================
# PROTECTED - PROFILE
# ============================================================

@app.get(
    "/protected/profile",
    summary="Get current user profile",
)
def profile(current_user=Depends(get_current_user)):

    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }


# ============================================================
# PROTECTED - DASHBOARD
# ============================================================

@app.get(
    "/protected/dashboard",
    summary="Get protected dashboard",
)
def dashboard(current_user=Depends(get_current_user)):

    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": current_user.id,
        "email": current_user.email,
    }


# ============================================================
# AUTH - LOGOUT
# ============================================================

@app.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
        )

    try:
        # Verify that the token belongs to a valid user first.
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # Supabase's Python client manages sign-out for its
        # current session. The token has already been verified
        # above, so the API returns 204 after successful validation.
        return None

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ============================================================
# TASK CRUD
# ============================================================

@app.get(
    "/tasks",
    summary="List all tasks",
    description="Returns all tasks stored in PostgreSQL.",
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
            content={
                "error": f"Task {task_id} not found"
            },
        )

    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task in PostgreSQL.",
)
def create_task(body: dict):

    title = body.get("title")

    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error": "Title is required and cannot be empty"
            },
        )

    return service.create_task(title)


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
)
def update_task(task_id: int, body: dict):

    result = service.update_task(task_id, body)

    if result is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": f"Task {task_id} not found"
            },
        )

    if "error" in result:
        return JSONResponse(
            status_code=400,
            content={
                "error": result["error"]
            },
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
            content={
                "error": f"Task {task_id} not found"
            },
        )

    return None