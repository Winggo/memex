import discord


class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f"[Discord] logged on as {self.user}")

    async def on_message(self, message):
        print(f"[Discord] message received from {message.author}")


intents = discord.Intents.default()
intents.message_content = True

discord_client = DiscordClient(intents=intents)
