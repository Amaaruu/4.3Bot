import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MusicCommunityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        await self.tree.sync()
        print("Cogs cargados y Slash Commands sincronizados.")

bot = MusicCommunityBot()

@bot.event
async def on_ready():
    print(f'Bot {bot.user} conectado y 100% operativo.')

if __name__ == '__main__':
    bot.run(TOKEN)