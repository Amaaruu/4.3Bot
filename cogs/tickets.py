import discord
from discord.ext import commands
from discord import app_commands
import chat_exporter
import io
import asyncio

claim_locks: dict[int, asyncio.Lock] = {}

TICKET_CONFIG = {
    "Rango Artista": {
        "emoji": "🎤",
        "color": discord.Color.green(),
        "descripcion": "Describe tu trayectoria artística. El staff revisará tu solicitud.",
        "rol_staff": "Staff",
    },
    "Rango Productor": {
        "emoji": "🎹",
        "color": discord.Color.blue(),
        "descripcion": "Comparte 2 trabajos previos (links de YouTube, archivos, etc.). No se acepta Google Drive.",
        "rol_staff": "Staff",
    },
    "Comprar Productos Exclusivos": {
        "emoji": "💎",
        "color": discord.Color.gold(),
        "descripcion": "Indica qué producto deseas adquirir y el staff te asistirá.",
        "rol_staff": "Staff",
    },
    "Compra VIP": {
        "emoji": "👑",
        "color": discord.Color.purple(),
        "descripcion": "Describe el plan VIP que te interesa. El equipo te contactará.",
        "rol_staff": "Staff",
    },
    "Soporte": {
        "emoji": "🛠️",
        "color": discord.Color.orange(),
        "descripcion": "Describe tu problema con el mayor detalle posible.",
        "rol_staff": "Staff",
    },
}

async def get_log_channel(guild: discord.Guild):
    return discord.utils.get(guild.text_channels, name="logs")

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nombre, emoji=cfg["emoji"])
            for nombre, cfg in TICKET_CONFIG.items()
        ]
        super().__init__(
            placeholder="Selecciona la categoría de tu ticket...",
            min_values=1, max_values=1,
            options=options,
            custom_id="ticket_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        categoria = self.values[0]
        cfg = TICKET_CONFIG[categoria]
        guild = interaction.guild

        async with interaction.client.db_pool.acquire() as conn:
            has_ticket = await conn.fetchval("SELECT channel_id FROM ticket_openers WHERE user_id = $1", interaction.user.id)
            if has_ticket:
                canal = guild.get_channel(has_ticket)
                if canal:
                    await interaction.response.send_message(f"Ya tienes un ticket abierto: {canal.mention}", ephemeral=True)
                    return
                else:
                    await conn.execute("DELETE FROM ticket_openers WHERE user_id = $1", interaction.user.id)

        ticket_category = discord.utils.get(guild.categories, name="TICKETS")
        if not ticket_category:
            ticket_category = await guild.create_category("TICKETS")

        staff_role = discord.utils.get(guild.roles, name=cfg["rol_staff"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=ticket_category,
            overwrites=overwrites
        )

        async with interaction.client.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO ticket_openers (channel_id, user_id, category) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                channel.id, interaction.user.id, categoria
            )

        embed = discord.Embed(
            title=f"{cfg['emoji']} {categoria}",
            description=f"Hola {interaction.user.mention}\n\n{cfg['descripcion']}",
            color=cfg["color"]
        )
        embed.set_footer(text="El staff te atenderá a la brevedad • Usa los botones para gestionar el ticket.")
        await channel.send(embed=embed, view=CloseAndClaimView())

        log_channel = await get_log_channel(guild)
        if log_channel:
            log_embed = discord.Embed(title="🎫 Nuevo Ticket", color=discord.Color.green())
            log_embed.add_field(name="Usuario", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
            log_embed.add_field(name="Categoría", value=categoria)
            log_embed.add_field(name="Canal", value=channel.mention)
            log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(f"✅ Ticket creado: {channel.mention}", ephemeral=True)


class ClaimButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reclamar", style=discord.ButtonStyle.primary, emoji="✋", custom_id="ticket_claim")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Solo el staff puede reclamar tickets.", ephemeral=True)
            return

        channel_id = interaction.channel_id
        lock = claim_locks.setdefault(channel_id, asyncio.Lock())

        if lock.locked():
            await interaction.response.send_message("El ticket está siendo reclamado ahora mismo.", ephemeral=True)
            return

        async with lock:
            async with interaction.client.db_pool.acquire() as conn:
                existing = await conn.fetchrow("SELECT staff_id FROM ticket_claims WHERE channel_id = $1", channel_id)
                if existing:
                    member = interaction.guild.get_member(existing['staff_id'])
                    name = member.display_name if member else f"ID {existing['staff_id']}"
                    await interaction.response.send_message(f"Este ticket ya fue reclamado por **{name}**.", ephemeral=True)
                    return
                await conn.execute(
                    "INSERT INTO ticket_claims (channel_id, staff_id) VALUES ($1, $2)",
                    channel_id, interaction.user.id
                )
                opener = await conn.fetchrow("SELECT user_id FROM ticket_openers WHERE channel_id = $1", channel_id)

            for member_id, overwrite in list(interaction.channel.overwrites.items()):
                if isinstance(member_id, discord.Member) and member_id.guild_permissions.manage_messages and member_id != interaction.user:
                    await interaction.channel.set_permissions(member_id, overwrite=None)

            if opener:
                opener_member = interaction.guild.get_member(opener['user_id'])
                if opener_member:
                    await interaction.channel.set_permissions(opener_member, read_messages=True, send_messages=True, attach_files=True)

            await interaction.channel.set_permissions(interaction.user, read_messages=True, send_messages=True, manage_messages=True)

            embed = discord.Embed(description=f"✋ Ticket reclamado por {interaction.user.mention}", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)


class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cerrar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Solo el staff puede cerrar tickets.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Cerrando ticket, recopilando transcripción...", ephemeral=True)

        async with interaction.client.db_pool.acquire() as conn:
            opener_record = await conn.fetchrow("SELECT user_id, category FROM ticket_openers WHERE channel_id = $1", interaction.channel_id)
            claim_record = await conn.fetchrow("SELECT staff_id FROM ticket_claims WHERE channel_id = $1", interaction.channel_id)

        transcript = await chat_exporter.export(interaction.channel)

        if opener_record:
            opener_member = interaction.guild.get_member(opener_record['user_id'])
            if opener_member and transcript:
                try:
                    transcript_file = discord.File(
                        io.BytesIO(transcript.encode()),
                        filename=f"transcript-{interaction.channel.name}.html"
                    )
                    dm_embed = discord.Embed(
                        title="🔒 Tu ticket ha sido cerrado",
                        color=discord.Color.red()
                    )
                    dm_embed.add_field(name="Categoría", value=opener_record['category'] or "N/A", inline=True)
                    dm_embed.add_field(name="Canal", value=interaction.channel.name, inline=True)
                    if claim_record:
                        staff_member = interaction.guild.get_member(claim_record['staff_id'])
                        dm_embed.add_field(name="Atendido por", value=staff_member.display_name if staff_member else "Staff", inline=True)
                    dm_embed.add_field(name="Cerrado en", value=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"), inline=False)
                    dm_embed.set_footer(text="Se adjunta la transcripción completa del ticket.")
                    await opener_member.send(embed=dm_embed, file=transcript_file)
                except discord.Forbidden:
                    pass

        log_channel = await get_log_channel(interaction.guild)
        if log_channel and transcript:
            transcript_log = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{interaction.channel.name}.html"
            )
            log_embed = discord.Embed(title="📁 Ticket Cerrado", color=discord.Color.orange())
            log_embed.add_field(name="Canal", value=interaction.channel.name, inline=True)
            log_embed.add_field(name="Categoría", value=opener_record['category'] if opener_record else "N/A", inline=True)
            if opener_record:
                opener_member = interaction.guild.get_member(opener_record['user_id'])
                log_embed.add_field(name="Abierto por", value=opener_member.mention if opener_member else str(opener_record['user_id']), inline=False)
            log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await log_channel.send(embed=log_embed, file=transcript_log)

        async with interaction.client.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM ticket_claims WHERE channel_id = $1", interaction.channel_id)
            await conn.execute("DELETE FROM ticket_openers WHERE channel_id = $1", interaction.channel_id)

        if interaction.channel_id in claim_locks:
            del claim_locks[interaction.channel_id]

        await interaction.channel.delete()


class CloseAndClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ClaimButton())
        self.add_item(CloseButton())


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_tickets")
    @commands.has_permissions(administrator=True)
    async def panel_tickets(self, ctx):
        desc = (
            "Abre un ticket según tu necesidad seleccionando la categoría correspondiente.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🎤 **Rango Artista / 🎹 Rango Productor**\n"
            "Para solicitar ambos rangos, abre un solo ticket e indícalo.\n\n"
            "🎹 **Para Rango Productor:**\n"
            "Debes compartir 2 trabajos previos (YouTube, archivos, etc.)\n"
            "🚫 Google Drive no será revisado.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ **Tickets falsos o trolls no serán tolerados.**\n"
            "La administración se reserva el derecho de admisión."
        )
        embed = discord.Embed(
            title="🎵 Sistema de Tickets",
            description=desc,
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Administración • Selecciona tu categoría abajo")
        await ctx.send(embed=embed, view=TicketView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))