import discord
from discord.ext import commands
from discord import app_commands

class PerfilModal(discord.ui.Modal, title='Editar Perfil Musical'):
    genero = discord.ui.TextInput(label='Género Musical', placeholder='Ej: HyperPop, Trap, House', required=False, max_length=50)
    daw = discord.ui.TextInput(label='DAW Favorito', placeholder='Ej: FL Studio, Ableton, Logic', required=False, max_length=50)
    redes = discord.ui.TextInput(label='Redes Sociales', placeholder='Instagram: @usuario, Twitter: @usuario', required=False, max_length=100)
    servicios = discord.ui.TextInput(label='Servicios Ofrecidos', placeholder='Ej: Mix & Master, Venta de Beats', style=discord.TextStyle.paragraph, required=False, max_length=300)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO perfiles (user_id, genero, daw, redes, servicios)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                genero = EXCLUDED.genero,
                daw = EXCLUDED.daw,
                redes = EXCLUDED.redes,
                servicios = EXCLUDED.servicios
            """, interaction.user.id, self.genero.value, self.daw.value, self.redes.value, self.servicios.value)
        await interaction.response.send_message("Perfil actualizado con éxito.", ephemeral=True)

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Mira tu perfil musical o el de otro usuario")
    async def perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        user = usuario or interaction.user
        async with self.bot.db_pool.acquire() as conn:
            record = await conn.fetchrow("SELECT * FROM perfiles WHERE user_id = $1", user.id)
        
        embed = discord.Embed(title=f"Perfil Musical | {user.display_name}", color=discord.Color.purple())
        embed.set_thumbnail(url=user.display_avatar.url)
        
        if record:
            embed.add_field(name="🎹 Género", value=record['genero'] or "No especificado", inline=True)
            embed.add_field(name="💻 DAW", value=record['daw'] or "No especificado", inline=True)
            embed.add_field(name="⭐ Reputación", value=str(record['reputacion']), inline=True)
            embed.add_field(name="🎵 Tracks Subidos", value=str(record['tracks']), inline=True)
            embed.add_field(name="📱 Redes Sociales", value=record['redes'] or "No especificado", inline=False)
            embed.add_field(name="💼 Servicios Ofrecidos", value=record['servicios'] or "Ninguno especificado", inline=False)
        else:
            embed.description = "Este usuario aún no ha configurado su perfil. Usa `/editarperfil`."
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="editarperfil", description="Configura tu perfil musical de artista/productor")
    async def editarperfil(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PerfilModal(self.bot))

async def setup(bot):
    await bot.add_cog(Profile(bot))