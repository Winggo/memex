import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(".env")
from src.discord_client import discord_client
from src.routes.api import router as api_router
from src.ws_listener import start_ws_listener


@asynccontextmanager
async def lifespan(server: FastAPI):
    loop = asyncio.get_event_loop()

    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
        loop.create_task(discord_client.start(os.environ["DISCORD_BOT_TOKEN"]))

    if os.environ.get("ENABLE_WEBSOCKET_LISTENER") == "true":
        loop.create_task(start_ws_listener())

    yield

    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
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
