from fastapi import FastAPI
from database import engine
from api.routers import subscriptions, users, auth

app = FastAPI()

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)

app.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
