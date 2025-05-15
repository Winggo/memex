import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(".env")
from src.discord_client import discord_client
from src.routes.api import router as api_router


@asynccontextmanager
async def lifespan(server: FastAPI):
    loop = asyncio.get_event_loop()
    loop.create_task(discord_client.start(os.environ["DISCORD_BOT_TOKEN"]))
    yield
    await discord_client.close()


server = FastAPI(lifespan=lifespan)
origins = []
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

server.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:server", host="0.0.0.0", port=8000, reload=True)
