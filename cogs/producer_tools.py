import discord
from discord.ext import commands
from discord import app_commands
import re

ALLOWED_HOSTS = ["mediafire.com", "mega.nz", "drive.google.com", "dropbox.com", "wetransfer.com", "gofile.io", "pixeldrain.com"]
LINK_REGEX = re.compile(r"https?://\S+")

def validate_link(link: str) -> bool:
    return any(host in link for host in ALLOWED_HOSTS)

class SharePackStaticView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ver Contraseña", style=discord.ButtonStyle.secondary, emoji="🔑", custom_id="sp_copy_pass_btn")
    async def copy_pass(self, interaction: discord.Interaction, button: discord.ui.Button):
        footer_text = interaction.message.embeds[0].footer.text
        try:
            pack_id = int(footer_text.split("Pack ID: ")[1].split(" •")[0])
        except (IndexError, ValueError):
            return await interaction.response.send_message("Error al obtener el ID del pack.", ephemeral=True)

        async with interaction.client.db_pool.acquire() as conn:
            record = await conn.fetchrow("SELECT password FROM share_packs WHERE id = $1", pack_id)
        if record and record['password']:
            await interaction.response.send_message(f"🔑 Contraseña: `{record['password']}`", ephemeral=True)
        else:
            await interaction.response.send_message("Este pack no tiene contraseña.", ephemeral=True)

    @discord.ui.button(label="Reportar", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="sp_report_pack_btn")
    async def report_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        footer_text = interaction.message.embeds[0].footer.text
        try:
            pack_id = int(footer_text.split("Pack ID: ")[1].split(" •")[0])
        except (IndexError, ValueError):
            return await interaction.response.send_message("Error al obtener el ID del pack.", ephemeral=True)

        try:
            async with interaction.client.db_pool.acquire() as conn:
                already = await conn.fetchval("SELECT reported FROM share_packs WHERE id = $1", pack_id)
                if already:
                    await interaction.response.send_message("Este pack ya fue reportado anteriormente.", ephemeral=True)
                    return
                await conn.execute("UPDATE share_packs SET reported = TRUE WHERE id = $1", pack_id)

            log_channel = discord.utils.get(interaction.guild.text_channels, name="logs")
            if log_channel:
                report_embed = discord.Embed(title="🚨 Pack Reportado", color=discord.Color.red())
                report_embed.add_field(name="Pack ID", value=str(pack_id), inline=True)
                report_embed.add_field(name="Reportado por", value=interaction.user.mention, inline=True)
                report_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
                await log_channel.send(embed=report_embed)

            await interaction.response.send_message("✅ Pack reportado a los moderadores. Gracias.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Error al reportar.", ephemeral=True)

class SharePackModal(discord.ui.Modal, title='📦 Compartir Sample Pack'):
    nombre = discord.ui.TextInput(label='Nombre del Pack', placeholder='Ej: Dark Trap Essentials Vol.1', max_length=100)
    descripcion = discord.ui.TextInput(
        label='Descripción',
        style=discord.TextStyle.paragraph,
        placeholder='Qué contiene el pack...',
        max_length=400
    )
    genero = discord.ui.TextInput(label='Género / Estilo', placeholder='Ej: Trap, House, Drill, R&B...', max_length=60)
    link = discord.ui.TextInput(label='Link de Descarga', placeholder='Mediafire, Mega, Drive, Dropbox, etc.')
    password = discord.ui.TextInput(label='Contraseña (Opcional)', placeholder='Déjalo vacío si no tiene contraseña', required=False, max_length=100)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        if not LINK_REGEX.match(self.link.value) or not validate_link(self.link.value):
            await interaction.response.send_message(
                f"❌ El link no es válido. Hosts permitidos: `{', '.join(ALLOWED_HOSTS)}`",
                ephemeral=True
            )
            return

        password_val = self.password.value.strip() if self.password.value else None

        try:
            async with self.bot.db_pool.acquire() as conn:
                pack_id = await conn.fetchval(
                    "INSERT INTO share_packs (user_id, nombre, descripcion, genero, link, password) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
                    interaction.user.id, self.nombre.value, self.descripcion.value,
                    self.genero.value, self.link.value, password_val
                )
                await conn.execute(
                    "INSERT INTO perfiles (user_id, tracks) VALUES ($1, 1) ON CONFLICT (user_id) DO UPDATE SET tracks = perfiles.tracks + 1",
                    interaction.user.id
                )

            embed = discord.Embed(title=f"📦 {self.nombre.value}", color=discord.Color.purple())
            embed.add_field(name="🎧 Género", value=self.genero.value, inline=True)
            embed.add_field(name="👤 Compartido por", value=interaction.user.mention, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="📝 Descripción", value=self.descripcion.value, inline=False)
            if password_val:
                embed.add_field(name="🔑 Contraseña", value="*(Oculta en el botón)*", inline=False)
            embed.set_footer(text=f"Pack ID: {pack_id} • {discord.utils.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")

            view = SharePackStaticView()
            view.add_item(discord.ui.Button(label="Descargar", style=discord.ButtonStyle.link, url=self.link.value, emoji="📥"))

            await interaction.response.send_message(embed=embed, view=view)

            log_channel = discord.utils.get(interaction.guild.text_channels, name="logs")
            if log_channel:
                log_embed = discord.Embed(title="📦 Nuevo Pack Compartido", color=discord.Color.green())
                log_embed.add_field(name="Usuario", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
                log_embed.add_field(name="Pack", value=self.nombre.value)
                log_embed.add_field(name="ID", value=str(pack_id))
                log_embed.add_field(name="Link", value=self.link.value, inline=False)
                log_embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
                await log_channel.send(embed=log_embed)

        except Exception:
            await interaction.response.send_message("❌ Error al guardar el pack. Intenta nuevamente.", ephemeral=True)

class ProducerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="share_pack", description="Comparte un Sample/Loop Pack con la comunidad")
    async def share_pack(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SharePackModal(self.bot))

    @app_commands.command(name="feedback", description="Sube tu maqueta para recibir feedback de la comunidad")
    async def feedback(self, interaction: discord.Interaction, link: str, genero: str):
        if not LINK_REGEX.match(link):
            await interaction.response.send_message("❌ Por favor proporciona un enlace válido.", ephemeral=True)
            return

        embed = discord.Embed(title="🎧 Maqueta Lista para Feedback", color=discord.Color.purple())
        embed.add_field(name="👤 Productor", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎵 Género", value=genero, inline=True)
        embed.add_field(name="🔗 Escuchar", value=f"[Abrir link]({link})", inline=False)
        embed.set_footer(text="Reacciona y deja tu comentario en el hilo de feedback.")

        await interaction.response.send_message("✅ Publicando tu maqueta...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)

        for emoji in ["🔥", "🎧", "📝", "🎹", "❤️"]:
            await msg.add_reaction(emoji)

        await msg.create_thread(name=f"Feedback — {interaction.user.display_name}")

async def setup(bot):
    await bot.add_cog(ProducerTools(bot))