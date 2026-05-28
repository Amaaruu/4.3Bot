import discord
from discord.ext import commands
from discord import app_commands

class PerfilModal(discord.ui.Modal, title='✏️ Editar Perfil Musical'):
    genero = discord.ui.TextInput(label='Género Musical', placeholder='Ej: HyperPop, Trap, House...', required=False, max_length=50)
    daw = discord.ui.TextInput(label='DAW Favorito', placeholder='Ej: FL Studio, Ableton, Logic Pro...', required=False, max_length=50)
    redes = discord.ui.TextInput(label='Redes Sociales', placeholder='IG: @usuario | Twitter: @usuario', required=False, max_length=150)
    servicios = discord.ui.TextInput(
        label='Servicios Ofrecidos',
        placeholder='Ej: Mix & Master, Venta de Beats, Ghostwriting...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=300
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            async with self.bot.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO perfiles (user_id, genero, daw, redes, servicios)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id) DO UPDATE SET
                        genero = EXCLUDED.genero,
                        daw = EXCLUDED.daw,
                        redes = EXCLUDED.redes,
                        servicios = EXCLUDED.servicios
                """, interaction.user.id, self.genero.value or None, self.daw.value or None,
                    self.redes.value or None, self.servicios.value or None)
            await interaction.response.send_message("✅ Perfil actualizado correctamente.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Error al guardar. Intenta nuevamente.", ephemeral=True)


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_profile(self, conn, user_id: int):
        await conn.execute(
            "INSERT INTO perfiles (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id
        )

    @app_commands.command(name="perfil", description="Muestra tu perfil musical o el de otro usuario")
    async def perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        user = usuario or interaction.user
        try:
            async with self.bot.db_pool.acquire() as conn:
                await self.ensure_profile(conn, user.id)
                record = await conn.fetchrow("SELECT * FROM perfiles WHERE user_id = $1", user.id)

            embed = discord.Embed(title=f"🎵 Perfil de {user.display_name}", color=discord.Color.purple())
            embed.set_thumbnail(url=user.display_avatar.url)

            embed.add_field(name="🎹 Género", value=record['genero'] or "—", inline=True)
            embed.add_field(name="💻 DAW", value=record['daw'] or "—", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="⭐ Reputación", value=f"`{record['reputacion']}`", inline=True)
            embed.add_field(name="🎵 Tracks", value=f"`{record['tracks']}`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="📱 Redes", value=record['redes'] or "—", inline=False)
            embed.add_field(name="💼 Servicios", value=record['servicios'] or "—", inline=False)
            embed.set_footer(text=f"ID: {user.id}")

            await interaction.response.send_message(embed=embed)
        except Exception:
            await interaction.response.send_message("❌ Error al obtener el perfil.", ephemeral=True)

    @app_commands.command(name="editarperfil", description="Configura tu perfil musical")
    async def editarperfil(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PerfilModal(self.bot))

    @app_commands.command(name="reputacion", description="[STAFF] Suma o resta reputación a un usuario")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(usuario="Usuario objetivo", accion="add o remove", cantidad="Puntos a modificar")
    async def reputacion(self, interaction: discord.Interaction, usuario: discord.Member, accion: str, cantidad: int):
        if accion.lower() not in ("add", "remove"):
            await interaction.response.send_message("La acción debe ser `add` o `remove`.", ephemeral=True)
            return
        if cantidad <= 0:
            await interaction.response.send_message("La cantidad debe ser mayor a 0.", ephemeral=True)
            return

        delta = cantidad if accion.lower() == "add" else -cantidad
        try:
            async with self.bot.db_pool.acquire() as conn:
                await self.ensure_profile(conn, usuario.id)
                new_rep = await conn.fetchval(
                    "UPDATE perfiles SET reputacion = reputacion + $1 WHERE user_id = $2 RETURNING reputacion",
                    delta, usuario.id
                )

            symbol = "+" if delta > 0 else ""
            embed = discord.Embed(title="⭐ Reputación Actualizada", color=discord.Color.purple())
            embed.add_field(name="Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="Cambio", value=f"`{symbol}{delta}`", inline=True)
            embed.add_field(name="Total", value=f"`{new_rep}`", inline=True)
            embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await interaction.response.send_message(embed=embed)

            log_channel = discord.utils.get(interaction.guild.text_channels, name="logs")
            if log_channel:
                await log_channel.send(embed=embed)
        except Exception:
            await interaction.response.send_message("❌ Error al actualizar la reputación.", ephemeral=True)

    @app_commands.command(name="tracks", description="[STAFF] Ajusta el contador de tracks de un usuario")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(usuario="Usuario objetivo", accion="add o remove", cantidad="Tracks a modificar")
    async def tracks(self, interaction: discord.Interaction, usuario: discord.Member, accion: str, cantidad: int):
        if accion.lower() not in ("add", "remove"):
            await interaction.response.send_message("La acción debe ser `add` o `remove`.", ephemeral=True)
            return
        if cantidad <= 0:
            await interaction.response.send_message("La cantidad debe ser mayor a 0.", ephemeral=True)
            return

        delta = cantidad if accion.lower() == "add" else -cantidad
        try:
            async with self.bot.db_pool.acquire() as conn:
                await self.ensure_profile(conn, usuario.id)
                new_tracks = await conn.fetchval(
                    "UPDATE perfiles SET tracks = GREATEST(0, tracks + $1) WHERE user_id = $2 RETURNING tracks",
                    delta, usuario.id
                )
            embed = discord.Embed(title="🎵 Tracks Actualizados", color=discord.Color.purple())
            embed.add_field(name="Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="Total", value=f"`{new_tracks}`", inline=True)
            embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
            await interaction.response.send_message(embed=embed)
        except Exception:
            await interaction.response.send_message("❌ Error al actualizar los tracks.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profile(bot))