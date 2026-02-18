from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models so they are registered with Base.metadata
import api.app.models  # noqa: F401
from api.app.database import Base, engine
from api.app.routers import auth, debts, expenses, groups, members
from api.app.variables import MyVariables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (dev convenience). Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=MyVariables.app_name,
    description=MyVariables.app_description,
    version=MyVariables.app_version,
    lifespan=lifespan,
    debug=MyVariables.debug,
)

# CORS configuration from environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=MyVariables.cors_origins,
    allow_credentials=MyVariables.cors_credentials,
    allow_methods=MyVariables.cors_methods,
    allow_headers=MyVariables.cors_headers,
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

    uvicorn.run(
        "app.main:app",
        host=MyVariables.server_host,
        port=MyVariables.server_port,
        reload=MyVariables.server_reload,
    )
