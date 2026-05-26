import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import timedelta
from collections import defaultdict
import time

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = re.compile(r"(https?://\S+)")
        self.allowed_links = ["soundcloud.com", "spotify.com", "youtube.com", "youtu.be", "drive.google.com"]
        self.user_messages = defaultdict(list)

    @app_commands.command(name="ban", description="Banea a un usuario")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        await usuario.ban(reason=razon)
        embed = discord.Embed(title="🔨 Usuario Baneado", description=f"{usuario.mention} ha sido baneado.\n**Razón:** {razon}", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Expulsa a un usuario")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        await usuario.kick(reason=razon)
        embed = discord.Embed(title="👢 Usuario Expulsado", description=f"{usuario.mention} ha sido expulsado.\n**Razón:** {razon}", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Aisla/Silencia a un usuario temporalmente")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, razon: str):
        await usuario.timeout(timedelta(minutes=minutos), reason=razon)
        embed = discord.Embed(title="⏱️ Usuario Aislado", description=f"{usuario.mention} ha sido silenciado por {minutos} minutos.\n**Razón:** {razon}", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Advierte a un usuario")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute("INSERT INTO warns (user_id, moderator_id, reason) VALUES ($1, $2, $3)", usuario.id, interaction.user.id, razon)
        embed = discord.Embed(title="⚠️ Advertencia", description=f"{usuario.mention} ha sido advertido.\n**Razón:** {razon}", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unwarn", description="Remueve una advertencia mediante ID")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, warn_id: int):
        async with self.bot.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM warns WHERE id = $1", warn_id)
        if result == "DELETE 0":
            await interaction.response.send_message("ID de advertencia no encontrada.", ephemeral=True)
            return
        embed = discord.Embed(title="✅ Advertencia Removida", description=f"Se ha eliminado la advertencia ID: {warn_id}", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lock", description="Bloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = discord.Embed(title="🔒 Canal Bloqueado", description="Este canal ha sido bloqueado temporalmente por moderación.", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlock", description="Desbloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        embed = discord.Embed(title="🔓 Canal Desbloqueado", description="Este canal ha sido desbloqueado.", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Limpia una cantidad de mensajes")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, cantidad: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=cantidad)
        await interaction.followup.send(f"Se han eliminado {cantidad} mensajes.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None or message.author.guild_permissions.manage_messages:
            return

        current_time = time.time()
        user_msgs = self.user_messages[message.author.id]
        user_msgs.append(current_time)
        self.user_messages[message.author.id] = [msg_time for msg_time in user_msgs if current_time - msg_time < 5]

        if len(self.user_messages[message.author.id]) > 5:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="Anti-Spam / Anti-Flood detectado")
            await message.channel.send(f"⏱️ {message.author.mention} ha sido silenciado por 5 minutos por Spam/Flood.", delete_after=10)
            return

        links = self.url_regex.findall(message.content)
        for link in links:
            if not any(allowed in link for allowed in self.allowed_links):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, ese enlace no está permitido por el filtro Anti-Links.", delete_after=5)
                return

async def setup(bot):
    await bot.add_cog(Moderation(bot))