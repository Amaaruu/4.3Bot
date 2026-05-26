import discord
from discord.ext import commands
from discord import app_commands

class ProducerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="feedback", description="Sube tu maqueta para recibir feedback de la comunidad")
    async def feedback(self, interaction: discord.Interaction, link: str, genero: str):
        embed = discord.Embed(title="🎧 Nueva Maqueta para Feedback", color=discord.Color.purple())
        embed.add_field(name="Productor", value=interaction.user.mention, inline=False)
        embed.add_field(name="Enlace", value=link, inline=False)
        embed.add_field(name="Género", value=genero, inline=False)
        
        await interaction.response.send_message("Generando panel de feedback...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        
        for emoji in ["🔥", "🎧", "📝", "🎹"]:
            await msg.add_reaction(emoji)
            
        await msg.create_thread(name=f"Feedback: {interaction.user.display_name}")

    @app_commands.command(name="share_loop", description="Comparte un Loop Kit con la comunidad")
    async def share_loop(self, interaction: discord.Interaction, nombre: str, link: str):
        embed = discord.Embed(title="📦 Nuevo Loop Compartido", color=discord.Color.purple())
        embed.add_field(name="Nombre del loop", value=nombre, inline=False)
        embed.add_field(name="Usuario que comparte", value=interaction.user.mention, inline=False)
        embed.add_field(name="Link del loop", value=link, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProducerTools(bot))