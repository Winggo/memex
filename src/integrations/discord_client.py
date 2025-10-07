import discord

from ..ai.rag_engine import respond_with_retrieved_context
from ..utils.constants import DISCORD_APP_ID


class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"[Discord] Logged on as {self.user}")

    async def on_message(self, message):
        if self.application_id != DISCORD_APP_ID or message.author.bot:
            return

        print(f"[Discord] Message received from {message.author}")
        completion = respond_with_retrieved_context(message.content)
        await message.channel.send(completion)


intents = discord.Intents.default()
intents.message_content = True

discord_client = DiscordClient(intents=intents)
