import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import timedelta
import time

STAFF_PERMISSIONS = app_commands.checks.has_permissions(manage_messages=True)

async def log_admin_action(guild: discord.Guild, embed: discord.Embed):
    channel = discord.utils.get(guild.text_channels, name="logs")
    if channel:
        await channel.send(embed=embed)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = re.compile(r"(https?://\S+)")
        self.allowed_links = ["soundcloud.com", "spotify.com", "youtube.com", "youtu.be", "drive.google.com", "mediafire.com", "mega.nz"]
        self.user_messages = {}

    @app_commands.command(name="ban", description="[STAFF] Banea a un usuario del servidor")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("No puedes banear a alguien con un rango igual o superior.", ephemeral=True)
            return
        await usuario.ban(reason=razon)
        embed = discord.Embed(title="🔨 Usuario Baneado", color=0x2b2d31)
        embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="kick", description="[STAFF] Expulsa a un usuario del servidor")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("No puedes expulsar a alguien con un rango igual o superior.", ephemeral=True)
            return
        await usuario.kick(reason=razon)
        embed = discord.Embed(title="👢 Usuario Expulsado", color=0x2b2d31)
        embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="timeout", description="[STAFF] Silencia a un usuario temporalmente")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, razon: str):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("No puedes silenciar a alguien con un rango igual o superior.", ephemeral=True)
            return
        await usuario.timeout(timedelta(minutes=minutos), reason=razon)
        embed = discord.Embed(title="⏱️ Usuario Silenciado", color=0x2b2d31)
        embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
        embed.add_field(name="Duración", value=f"{minutos} minuto(s)", inline=True)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="warn", description="[STAFF] Advierte a un usuario")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO warns (user_id, moderator_id, reason) VALUES ($1, $2, $3)",
                usuario.id, interaction.user.id, razon
            )
            total = await conn.fetchval("SELECT COUNT(*) FROM warns WHERE user_id = $1", usuario.id)
        embed = discord.Embed(title="⚠️ Advertencia Emitida", color=0x2b2d31)
        embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.add_field(name="Total de Warns", value=str(total), inline=True)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="unwarn", description="[STAFF] Elimina una advertencia por ID")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, warn_id: int):
        async with self.bot.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM warns WHERE id = $1", warn_id)
        if result == "DELETE 0":
            await interaction.response.send_message("No se encontró un warn con ese ID.", ephemeral=True)
            return
        embed = discord.Embed(title="✅ Advertencia Eliminada", description=f"Warn ID `{warn_id}` removido.", color=0x2b2d31)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="warns", description="[STAFF] Consulta las advertencias de un usuario")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warns(self, interaction: discord.Interaction, usuario: discord.Member):
        async with self.bot.db_pool.acquire() as conn:
            records = await conn.fetch("SELECT id, reason, timestamp FROM warns WHERE user_id = $1 ORDER BY timestamp DESC", usuario.id)
        embed = discord.Embed(title=f"📋 Warns de {usuario.display_name}", color=0x2b2d31)
        if not records:
            embed.description = "Este usuario no tiene advertencias."
        else:
            for r in records[:10]:
                embed.add_field(
                    name=f"ID #{r['id']} — {r['timestamp'].strftime('%d/%m/%Y')}",
                    value=r['reason'],
                    inline=False
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="lock", description="[STAFF] Bloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = discord.Embed(title="🔒 Canal Bloqueado", description="Este canal ha sido bloqueado temporalmente.", color=0x2b2d31)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="unlock", description="[STAFF] Desbloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        embed = discord.Embed(title="🔓 Canal Desbloqueado", description="El canal está nuevamente habilitado.", color=0x2b2d31)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await interaction.response.send_message(embed=embed)
        await log_admin_action(interaction.guild, embed)

    @app_commands.command(name="clear", description="[STAFF] Elimina una cantidad de mensajes")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, cantidad: int):
        if cantidad < 1 or cantidad > 100:
            await interaction.response.send_message("La cantidad debe estar entre 1 y 100.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=cantidad)
        await interaction.followup.send(f"🗑️ {len(deleted)} mensajes eliminados.", ephemeral=True)
        log_embed = discord.Embed(title="🗑️ Purge de Mensajes", color=0x2b2d31)
        log_embed.add_field(name="Canal", value=interaction.channel.mention)
        log_embed.add_field(name="Cantidad", value=str(len(deleted)))
        log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await log_admin_action(interaction.guild, log_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        if message.author.guild_permissions.manage_messages:
            return

        current_time = time.time()
        user_msgs = self.user_messages.get(message.author.id, [])
        user_msgs.append(current_time)
        valid_msgs = [t for t in user_msgs if current_time - t < 5]
        
        if not valid_msgs:
            self.user_messages.pop(message.author.id, None)
        else:
            self.user_messages[message.author.id] = valid_msgs

        if len(valid_msgs) > 5:
            self.user_messages.pop(message.author.id, None)
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="Anti-Spam automático")
            await message.channel.send(
                f"⏱️ {message.author.mention} fue silenciado por 5 minutos por flood/spam.",
                delete_after=8
            )
            return

        links = self.url_regex.findall(message.content)
        for link in links:
            if not any(allowed in link for allowed in self.allowed_links):
                await message.delete()
                await message.channel.send(
                    f"🚫 {message.author.mention} ese enlace no está permitido.",
                    delete_after=5
                )
                return

async def setup(bot):
    await bot.add_cog(Moderation(bot))