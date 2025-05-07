import discord

from rag_engine import respond_with_retrieved_context
from utils.constants import DISCORD_APP_ID


class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"[Discord] logged on as {self.user}")

    async def on_message(self, message):
        print(f"[Discord] message received from {message.author}")
        if self.application_id != DISCORD_APP_ID or message.author.bot:
            return
        
        completion = respond_with_retrieved_context(message.content)
        await message.channel.send(completion)


intents = discord.Intents.default()
intents.message_content = True

discord_client = DiscordClient(intents=intents)
