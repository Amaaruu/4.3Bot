import discord
from discord.ext import commands
from discord import app_commands

class ProducerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="feedback", description="Sube tu maqueta para recibir feedback de la comunidad.")
    @app_commands.describe(link="Enlace de tu track", daw="DAW que utilizaste", genero="Género musical")
    async def feedback(self, interaction: discord.Interaction, link: str, daw: str = "No especificado", genero: str = "Variado"):
        embed = discord.Embed(title="🎧 Nueva Maqueta para Feedback", color=discord.Color.purple())
        embed.add_field(name="Productor", value=interaction.user.mention, inline=False)
        embed.add_field(name="Enlace", value=link, inline=False)
        embed.add_field(name="DAW", value=daw, inline=True)
        embed.add_field(name="Género", value=genero, inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message("Procesando tu track...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        await msg.create_thread(name=f"Feedback: {interaction.user.display_name} - {genero}")

    @app_commands.command(name="share_loop", description="Comparte un Loop Kit o Sample Pack.")
    async def share_loop(self, interaction: discord.Interaction, nombre: str, link: str, libre_derechos: bool):
        color = discord.Color.green() if libre_derechos else discord.Color.red()
        estado = "✅ Libre de Derechos" if libre_derechos else "⚠️ Requiere Clearance"
        
        embed = discord.Embed(title="📦 Nuevo Pack Compartido", color=color)
        embed.add_field(name="Pack", value=nombre, inline=True)
        embed.add_field(name="Estado", value=estado, inline=True)
        embed.add_field(name="Enlace", value=link, inline=False)
        embed.set_footer(text=f"Aportado por {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="collab", description="Busca artistas o productores para colaborar.")
    @app_commands.choices(rol=[
        app_commands.Choice(name="Vocalista", value="Vocalista"),
        app_commands.Choice(name="Beatmaker", value="Beatmaker"),
        app_commands.Choice(name="Ingeniero de Mezcla", value="Ingeniero de Mezcla"),
        app_commands.Choice(name="Instrumentista", value="Instrumentista")
    ])
    async def collab(self, interaction: discord.Interaction, rol: app_commands.Choice[str], detalles: str):
        embed = discord.Embed(title="🤝 ¡Búsqueda de Colaboración!", color=discord.Color.gold())
        embed.description = f"{interaction.user.mention} está buscando un **{rol.value}**."
        embed.add_field(name="Detalles del Proyecto", value=detalles, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProducerTools(bot))