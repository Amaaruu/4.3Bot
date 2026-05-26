import discord
from discord.ext import commands
from discord import app_commands
import random

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="artistname", description="Genera una idea de nombre artístico")
    async def artistname(self, interaction: discord.Interaction):
        prefijos = ["Lil", "Young", "DJ", "MC", "Kid", "Saint", "Lord", "Yung", "Kidd", "Big"]
        sufijos = ["Beats", "Wave", "Synth", "Cloud", "Ghost", "Vibe", "God", "Star", "Space", "Boy"]
        nombre = f"{random.choice(prefijos)} {random.choice(sufijos)}"
        embed = discord.Embed(title="💡 Idea de Nombre Artístico", description=f"**{nombre}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lyricsidea", description="Genera una idea para escribir letras")
    async def lyricsidea(self, interaction: discord.Interaction):
        ideas = [
            "Una noche de insomnio en la ciudad", 
            "El precio de la fama y la soledad", 
            "Un amor que existió en una simulación", 
            "Superando la traición de un amigo", 
            "Vivir el momento sin pensar en el mañana",
            "La nostalgia de los veranos pasados"
        ]
        embed = discord.Embed(title="📝 Idea para Letra", description=f"**{random.choice(ideas)}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="beatidea", description="Genera una idea de concepto para un beat")
    async def beatidea(self, interaction: discord.Interaction):
        ideas = [
            "Samplear un bolero antiguo con baterías de trap moderno", 
            "Sintetizadores retro 80s con percusiones de reggaeton", 
            "Un beat de drill sin melodía, solo bajos 808 rítmicos y FX", 
            "Acordes de R&B oscuros con un BPM de drum and bass",
            "Guitarras acústicas lo-fi con hi-hats rápidos de trap"
        ]
        embed = discord.Embed(title="🎹 Idea para Beat", description=f"**{random.choice(ideas)}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="songname", description="Genera un título para tu canción")
    async def songname(self, interaction: discord.Interaction):
        nombres = ["Midnight Drive", "Lost Echoes", "Neon Tears", "Lucid Dreams", "Fading Shadows", "Digital Heartbreak", "No Return", "Static Signals"]
        embed = discord.Embed(title="🎵 Título para Canción", description=f"**{random.choice(nombres)}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bpm", description="Recomienda un BPM ideal según el género")
    async def bpm(self, interaction: discord.Interaction, genero: str):
        recomendaciones = {
            "trap": "130 - 150 BPM",
            "reggaeton": "85 - 100 BPM",
            "house": "120 - 130 BPM",
            "drill": "140 - 145 BPM",
            "boombap": "85 - 95 BPM",
            "hyperpop": "150 - 180 BPM",
            "rnb": "70 - 90 BPM",
            "techno": "125 - 140 BPM"
        }
        resultado = recomendaciones.get(genero.lower(), "100 - 120 BPM (Estándar/Pop)")
        embed = discord.Embed(title="⏱️ Recomendación de BPM", description=f"Para **{genero.title()}**, te sugiero: **{resultado}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scale", description="Recomienda una escala musical para el vibe deseado")
    async def scale(self, interaction: discord.Interaction, vibe: str):
        escalas = {
            "triste": "Menor Natural (Ej: Do Menor)",
            "oscuro": "Menor Armónica o Frigia (Ej: Mi Frigio)",
            "feliz": "Mayor Natural (Ej: Sol Mayor)",
            "epico": "Dórica (Ej: Re Dórico)",
            "melancolico": "Lidia (Ej: Fa Lidio)",
            "misterioso": "Locria (Ej: Si Locrio)"
        }
        resultado = escalas.get(vibe.lower(), "Menor Natural (Segura y versátil)")
        embed = discord.Embed(title="🎼 Recomendación de Escala", description=f"Para un vibe **{vibe.title()}**, te sugiero: **{resultado}**", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))