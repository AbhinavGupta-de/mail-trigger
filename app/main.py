from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database import connect_to_mongo, close_mongo_connection
from app.auth.dependencies import get_current_user_optional

# Import routers
from app.routes.auth import router as auth_router
from app.routes.templates import router as templates_router
from app.routes.recipients import router as recipients_router
from app.routes.email import router as email_router
from app.routes.admin import router as admin_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Email Trigger",
    description="Send templated emails to your warden via Gmail",
    version="1.0.0",
    lifespan=lifespan
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=86400 * 7  # 7 days
)

# Include API routers
app.include_router(auth_router)
app.include_router(templates_router)
app.include_router(recipients_router)
app.include_router(email_router)
app.include_router(admin_router)


# ==================== API INFO ====================

@app.get("/api/me")
async def get_me(request: Request):
    """Get current user info."""
    user = await get_current_user_optional(request)
    if not user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "is_admin": user.get("is_admin", False)
    }


# ==================== SERVE REACT BUILD (PRODUCTION) ====================

# In production, serve the React build
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_BUILD_DIR):
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")

    # Serve index.html for all other routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API or auth routes
        if full_path.startswith("api/") or full_path.startswith("auth/"):
            return {"detail": "Not found"}

        index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Frontend not built. Run 'npm run build' in frontend directory."}
