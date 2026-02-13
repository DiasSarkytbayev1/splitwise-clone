from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, groups, members, expenses, debts

# Import models so they are registered with Base.metadata
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (dev convenience). Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Expense Splitter API",
    description="A FastAPI backend for splitting expenses among groups of users.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(members.router)
app.include_router(expenses.router)
app.include_router(debts.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Expense Splitter API"}

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Ensure the project root is on sys.path so `app` is importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)