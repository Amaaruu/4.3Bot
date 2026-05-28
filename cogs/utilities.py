import discord
from discord.ext import commands
from discord import app_commands
import random

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="artistname", description="Genera una idea de nombre artístico")
    async def artistname(self, interaction: discord.Interaction):
        prefijos = ["Lil", "Young", "DJ", "MC", "Kid", "Saint", "Lord", "Yung", "Kidd", "Big", "Lil'", "King"]
        sufijos = ["Beats", "Wave", "Synth", "Cloud", "Ghost", "Vibe", "God", "Star", "Space", "Boy", "Soul", "Haze"]
        nombre = f"{random.choice(prefijos)} {random.choice(sufijos)}"
        embed = discord.Embed(title="💡 Nombre Artístico Generado", description=f"### {nombre}", color=discord.Color.purple())
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lyricsidea", description="Genera una idea para escribir letras")
    async def lyricsidea(self, interaction: discord.Interaction):
        ideas = [
            "Una noche de insomnio en la ciudad",
            "El precio de la fama y la soledad",
            "Un amor que existió en una simulación",
            "Superando la traición de un amigo cercano",
            "Vivir el momento sin pensar en el mañana",
            "La nostalgia de los veranos de la infancia",
            "Crecer sin figura paterna",
            "El vacío detrás del éxito",
            "Enamorarse de alguien que ya no existe",
        ]
        embed = discord.Embed(title="📝 Idea para Letra", description=f"### {random.choice(ideas)}", color=discord.Color.purple())
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="beatidea", description="Genera un concepto para un beat")
    async def beatidea(self, interaction: discord.Interaction):
        ideas = [
            "Samplear un bolero antiguo con baterías de trap moderno",
            "Sintetizadores retro 80s con percusiones de reggaeton",
            "Beat de drill sin melodía: solo 808s rítmicos y FX",
            "Acordes R&B oscuros a BPM de drum and bass",
            "Guitarras acústicas lo-fi con hi-hats rápidos de trap",
            "Piano minimalista con sub bass pesado y reverb infinito",
            "Sample de jazz cortado y repitchado sobre kicks 808",
        ]
        embed = discord.Embed(title="🎹 Concepto de Beat", description=f"### {random.choice(ideas)}", color=discord.Color.purple())
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="songname", description="Genera un título para tu canción")
    async def songname(self, interaction: discord.Interaction):
        nombres = ["Midnight Drive", "Lost Echoes", "Neon Tears", "Lucid Dreams", "Fading Shadows",
                   "Digital Heartbreak", "No Return", "Static Signals", "Cold Nights", "Glass Soul",
                   "Empty Frames", "Velvet Dark", "Parallel Lines", "Hollow Youth"]
        embed = discord.Embed(title="🎵 Título para Canción", description=f"### {random.choice(nombres)}", color=discord.Color.purple())
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bpm", description="Recomienda un BPM según el género")
    @app_commands.describe(genero="Género musical (trap, reggaeton, house, drill, etc.)")
    async def bpm(self, interaction: discord.Interaction, genero: str):
        recomendaciones = {
            "trap": "130 – 150 BPM",
            "reggaeton": "85 – 100 BPM",
            "house": "120 – 130 BPM",
            "drill": "140 – 145 BPM",
            "boombap": "85 – 95 BPM",
            "hyperpop": "150 – 180 BPM",
            "rnb": "70 – 90 BPM",
            "techno": "125 – 140 BPM",
            "afrobeat": "95 – 110 BPM",
            "dancehall": "90 – 110 BPM",
            "lofi": "70 – 90 BPM",
        }
        resultado = recomendaciones.get(genero.lower(), "100 – 120 BPM (Estándar/Pop)")
        embed = discord.Embed(title="⏱️ Recomendación de BPM", color=discord.Color.purple())
        embed.add_field(name="Género", value=genero.title(), inline=True)
        embed.add_field(name="BPM sugerido", value=f"**{resultado}**", inline=True)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scale", description="Recomienda una escala musical según el vibe")
    @app_commands.describe(vibe="Estado de ánimo (triste, oscuro, feliz, epico, melancolico, misterioso)")
    async def scale(self, interaction: discord.Interaction, vibe: str):
        escalas = {
            "triste": ("Menor Natural", "Ej: Do Menor — melancólico y emotivo"),
            "oscuro": ("Menor Armónica / Frigia", "Ej: Mi Frigio — tenso, oscuro, dramático"),
            "feliz": ("Mayor Natural", "Ej: Sol Mayor — brillante y energético"),
            "epico": ("Dórica", "Ej: Re Dórico — heroico con toque oscuro"),
            "melancolico": ("Lidia", "Ej: Fa Lidio — soñador y etéreo"),
            "misterioso": ("Locria", "Ej: Si Locrio — inestable y enigmático"),
            "romantico": ("Mayor con VII mayor", "Ej: La Mayor — cálido y emotivo"),
        }
        data = escalas.get(vibe.lower())
        if data:
            escala, nota = data
        else:
            escala, nota = "Menor Natural", "Versátil y segura para cualquier estilo"

        embed = discord.Embed(title="🎼 Escala Recomendada", color=discord.Color.purple())
        embed.add_field(name="Vibe", value=vibe.title(), inline=True)
        embed.add_field(name="Escala", value=f"**{escala}**", inline=True)
        embed.add_field(name="Nota", value=nota, inline=False)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))