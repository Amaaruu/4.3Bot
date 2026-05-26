import discord
from discord.ext import commands
from discord import app_commands

class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="alert", description="Envía una alerta oficial al servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def alert(self, interaction: discord.Interaction, titulo: str, mensaje: str):
        embed = discord.Embed(
            title=f"**{titulo}**", 
            description=mensaje, 
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Alerts(bot))