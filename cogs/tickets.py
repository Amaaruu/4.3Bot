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
        "descripcion": "Comparte tu trayectoria artística y ejemplos de tu trabajo. El equipo de staff revisará tu solicitud y se pondrá en contacto contigo.",
        "rol_staff": "Staff",
    },
    "Rango Productor": {
        "emoji": "🎹",
        "color": discord.Color.blue(),
        "descripcion": "Comparte al menos 2 trabajos previos (YouTube, SoundCloud o archivos de audio). Google Drive no será tomado en cuenta para la revisión.",
        "rol_staff": "Staff",
    },
    "Comprar Productos Exclusivos": {
        "emoji": "💎",
        "color": discord.Color.gold(),
        "descripcion": "Indica el producto exclusivo que deseas adquirir. Un miembro del equipo te asistirá personalmente con todos los detalles.",
        "rol_staff": "Staff",
    },
    "Compra VIP": {
        "emoji": "👑",
        "color": discord.Color.purple(),
        "descripcion": "Describe el plan VIP que te interesa. Nuestro equipo te contactará a la brevedad con toda la información necesaria.",
        "rol_staff": "Staff",
    },
    "Soporte Técnico": {
        "emoji": "🛠️",
        "color": discord.Color.orange(),
        "descripcion": "¿Tienes problemas con el servidor, los canales o el bot? Descríbenos el inconveniente con el mayor detalle posible.",
        "rol_staff": "Staff",
    },
    "Ayuda Técnica": {
        "emoji": "🎛️",
        "color": discord.Color.from_rgb(0, 160, 210),
        "descripcion": "¿Necesitas orientación con tu DAW, plugins o flujo de trabajo? Describe tu consulta y nuestra comunidad hará lo posible por ayudarte.",
        "rol_staff": "Staff",
    },
    "Problemas con Roles": {
        "emoji": "🏷️",
        "color": discord.Color.from_rgb(210, 105, 30),
        "descripcion": "¿Tu rol no fue asignado correctamente o perdiste acceso a algún canal? Indícanos el problema con detalle para resolverlo.",
        "rol_staff": "Staff",
    },
    "Consultas Generales": {
        "emoji": "💬",
        "color": discord.Color.from_rgb(80, 180, 120),
        "descripcion": "¿Tienes alguna pregunta, sugerencia o comentario sobre el servidor? Estamos aquí para escucharte.",
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
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        categoria = self.values[0]
        cfg = TICKET_CONFIG[categoria]
        guild = interaction.guild

        existing = discord.utils.find(
            lambda c: c.name.startswith(f"ticket-{interaction.user.name.lower()}"),
            guild.text_channels
        )
        if existing:
            await interaction.response.send_message(
                f"Ya tienes un ticket abierto: {existing.mention}", ephemeral=True
            )
            return

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
            title=f"{cfg['emoji']}  {categoria}",
            description=f"Hola, {interaction.user.mention}\n\n{cfg['descripcion']}",
            color=cfg["color"]
        )
        embed.set_footer(text="El staff te atenderá a la brevedad  •  Usa los botones para gestionar el ticket.")
        await channel.send(embed=embed, view=CloseAndClaimView())

        log_channel = await get_log_channel(guild)
        if log_channel:
            log_embed = discord.Embed(title="🎫 Nuevo Ticket Abierto", color=discord.Color.green())
            log_embed.add_field(name="Usuario", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
            log_embed.add_field(name="Categoría", value=categoria)
            log_embed.add_field(name="Canal", value=channel.mention)
            log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(f"✅ Ticket creado exitosamente: {channel.mention}", ephemeral=True)


class ClaimButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reclamar Ticket", style=discord.ButtonStyle.primary, emoji="✋", custom_id="ticket_claim")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Solo el staff puede reclamar tickets.", ephemeral=True)
            return

        channel_id = interaction.channel_id
        if channel_id not in claim_locks:
            claim_locks[channel_id] = asyncio.Lock()

        if claim_locks[channel_id].locked():
            await interaction.response.send_message("El ticket está siendo reclamado en este momento.", ephemeral=True)
            return

        async with claim_locks[channel_id]:
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

            embed = discord.Embed(
                description=f"✋  Ticket reclamado por {interaction.user.mention}. El staff te atenderá a continuación.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)


class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cerrar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Solo el staff puede cerrar tickets.", ephemeral=True)
            return

        await interaction.response.defer()

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
                    dm_embed.set_footer(text="Se adjunta la transcripción completa del ticket para tu referencia.")
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
            "Selecciona la categoría que mejor describa tu consulta.\n"
            "Un miembro del staff te atenderá en privado a la brevedad.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎤  **Rango Artista**\n"
            "Solicita tu verificación como artista mostrando tu trabajo.\n\n"
            "🎹  **Rango Productor**\n"
            "Comparte 2 trabajos previos para verificar tu rango.\n"
            "🚫  Google Drive no será revisado.\n\n"
            "💎  **Comprar Productos Exclusivos**\n"
            "Accede a nuestro catálogo de herramientas y recursos premium.\n\n"
            "👑  **Compra VIP**\n"
            "Desbloquea beneficios exclusivos con nuestros planes VIP.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛠️  **Soporte Técnico** — Problemas con el servidor, canales o el bot.\n"
            "🎛️  **Ayuda Técnica** — Orientación con tu DAW, plugins o flujo de trabajo.\n"
            "🏷️  **Problemas con Roles** — Errores en la asignación de roles o accesos.\n"
            "💬  **Consultas Generales** — Preguntas, sugerencias o cualquier inquietud.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️  Los tickets abiertos con mala intención serán cerrados\n"
            "y el usuario sancionado de forma inmediata.\n"
            "La administración se reserva el derecho de admisión."
        )
        embed = discord.Embed(
            title="🎫  Sistema de Tickets",
            description=desc,
            color=discord.Color.from_rgb(88, 24, 180)
        )
        embed.set_footer(text="Administración  •  Selecciona tu categoría en el menú de abajo")
        await ctx.send(embed=embed, view=TicketView())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Tickets(bot))