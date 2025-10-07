import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(".env")
from .routes.api import router as api_router


@asynccontextmanager
async def lifespan(server: FastAPI):
    loop = asyncio.get_event_loop()
    scheduler = None

    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
        from .integrations.discord_client import discord_client
        loop.create_task(discord_client.start(os.environ["DISCORD_BOT_TOKEN"]))

    if os.environ.get("ENABLE_WEBSOCKET_LISTENER") == "true":
        from .ws_listener import start_ws_listener
        loop.create_task(start_ws_listener())

    if os.environ.get("ENABLE_ASSISTANT") == "true":
        from .ai_assistant import start_assistant
        scheduler = start_assistant()

    yield

    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
        await discord_client.close()

    if scheduler:
        scheduler.shutdown()


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
    uvicorn.run("src.app:server", host="0.0.0.0", port=8000, reload=True)
