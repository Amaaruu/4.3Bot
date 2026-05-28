import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncpg
import traceback
from flask import Flask
from threading import Thread
from cogs.tickets import TicketView, CloseAndClaimView
from cogs.producer_tools import SharePackStaticView

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_server)
    t.start()

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
            if filename.endswith('.py') and filename != '__init__.py':
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        self.add_view(TicketView())
        self.add_view(CloseAndClaimView())
        self.add_view(SharePackStaticView())
        
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
                CREATE TABLE IF NOT EXISTS invites (
                    joined_id BIGINT PRIMARY KEY,
                    inviter_id BIGINT
                );
                CREATE TABLE IF NOT EXISTS share_packs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    nombre TEXT,
                    descripcion TEXT,
                    genero TEXT,
                    link TEXT,
                    password TEXT,
                    reported BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ticket_claims (
                    channel_id BIGINT PRIMARY KEY,
                    staff_id BIGINT,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ticket_openers (
                    channel_id BIGINT PRIMARY KEY,
                    user_id BIGINT,
                    category TEXT
                );
            """)

    async def on_tree_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message("⛔ Sin permisos suficientes.", ephemeral=True)
        else:
            traceback.print_exception(type(error), error, error.__traceback__)

bot = MusicCommunityBot()
bot.tree.on_error = bot.on_tree_error

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

if __name__ == '__main__':
    keep_alive()
    bot.run(TOKEN)