import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

COLOR_MAP = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "purple": discord.Color.purple(),
    "gold": discord.Color.gold(),
    "orange": discord.Color.orange(),
    "dark_red": discord.Color.dark_red(),
    "blurple": discord.Color.blurple(),
}


class AlertModal(discord.ui.Modal, title='📢 Nueva Alerta Oficial'):
    titulo = discord.ui.TextInput(label='Título', placeholder='Ej: Actualización importante del servidor', max_length=200)
    mensaje = discord.ui.TextInput(label='Mensaje', style=discord.TextStyle.paragraph, placeholder='Contenido de la alerta...')
    color_input = discord.ui.TextInput(label='Color (Opcional)', placeholder='red, blue, green, purple, gold, orange', required=False, max_length=20)
    imagen = discord.ui.TextInput(label='URL de Imagen (Opcional)', placeholder='https://...', required=False, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        color_key = self.color_input.value.lower().strip() if self.color_input.value else "purple"
        color = COLOR_MAP.get(color_key, discord.Color.purple())

        embed = discord.Embed(title=self.titulo.value, description=self.mensaje.value, color=color)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))

        if self.imagen.value and self.imagen.value.startswith("http"):
            embed.set_image(url=self.imagen.value)

        await interaction.response.send_message(embed=embed)

        log_channel = discord.utils.get(interaction.guild.text_channels, name="logs")
        if log_channel:
            log_embed = discord.Embed(title="📢 Alerta Enviada", color=discord.Color.blurple())
            log_embed.add_field(name="Enviada por", value=interaction.user.mention, inline=False)
            log_embed.add_field(name="Título", value=self.titulo.value, inline=False)
            log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await log_channel.send(embed=log_embed)


class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="alert", description="[ADMIN] Envía una alerta oficial al canal actual")
    @app_commands.checks.has_permissions(administrator=True)
    async def alert(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AlertModal())

    @app_commands.command(name="newdrop", description="[ADMIN] Anuncia un nuevo drop exclusivo con contador regresivo")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        dias="Días restantes para el drop",
        horas="Horas restantes para el drop",
        minutos="Minutos restantes para el drop"
    )
    async def newdrop(self, interaction: discord.Interaction, dias: int = 0, horas: int = 0, minutos: int = 0):
        if dias < 0 or horas < 0 or minutos < 0:
            await interaction.response.send_message("❌ Los valores no pueden ser negativos.", ephemeral=True)
            return

        total_seconds = (dias * 86400) + (horas * 3600) + (minutos * 60)
        if total_seconds <= 0:
            await interaction.response.send_message("❌ Debes especificar al menos 1 minuto de anticipación.", ephemeral=True)
            return

        drop_time = discord.utils.utcnow() + timedelta(seconds=total_seconds)

        embed = discord.Embed(
            title="⚡  NUEVO DROP EXCLUSIVO EN CAMINO",
            description=(
                "Algo que cambiará tu flujo de producción está a punto de llegar.\n"
                "Plugins, samples y herramientas de nivel profesional,\n"
                "curadas exclusivamente para los miembros de esta comunidad.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🔒  **Acceso exclusivo para miembros activos del servidor**\n"
                "🎛️  **Plugins · Samples · Packs · Recursos Premium**\n"
                "🔥  **Contenido de nivel profesional — sin costo para ti**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.from_rgb(138, 43, 226)
        )

        embed.add_field(
            name="⏳  CUENTA REGRESIVA",
            value=(
                f"Llega **{discord.utils.format_dt(drop_time, style='R')}**\n"
                f"📅  {discord.utils.format_dt(drop_time, style='F')}"
            ),
            inline=False
        )

        embed.add_field(
            name="🔔  ¿CÓMO NO PERDÉRTELO?",
            value=(
                "Activa las notificaciones de este canal y mantente pendiente de los anuncios.\n"
                "**El acceso al drop llega una sola vez — no te quedes fuera.**"
            ),
            inline=False
        )

        embed.set_footer(text="© Comunidad de Productores & Artistas Emergentes  •  DROP ALERT")

        await interaction.response.send_message(embed=embed)

        log_channel = discord.utils.get(interaction.guild.text_channels, name="logs")
        if log_channel:
            log_embed = discord.Embed(title="⚡ Nuevo Drop Anunciado", color=discord.Color.purple())
            log_embed.add_field(name="Anunciado por", value=interaction.user.mention, inline=False)
            log_embed.add_field(name="Fecha del Drop", value=discord.utils.format_dt(drop_time, style='F'), inline=False)
            log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await log_channel.send(embed=log_embed)


async def setup(bot):
    await bot.add_cog(Alerts(bot))