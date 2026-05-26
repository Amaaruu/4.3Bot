import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncpg
import traceback

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

class MusicCommunityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None
        )
        self.db_pool = None

    async def setup_hook(self):
        self.db_pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_db()

        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        await self.tree.sync()

    async def init_db(self):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS perfiles (
                    user_id BIGINT PRIMARY KEY,
                    genero TEXT,
                    daw TEXT,
                    redes TEXT,
                    reputacion INTEGER DEFAULT 0,
                    tracks INTEGER DEFAULT 0,
                    servicios TEXT
                );
                CREATE TABLE IF NOT EXISTS warns (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    moderator_id BIGINT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    async def on_tree_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        else:
            traceback.print_exception(type(error), error, error.__traceback__)

bot = MusicCommunityBot()
bot.tree.on_error = bot.on_tree_error

@bot.event
async def on_ready():
    pass

if __name__ == '__main__':
    bot.run(TOKEN)