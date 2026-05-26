import discord
from discord.ext import commands

class ProducerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def feedback(self, ctx, link: str):
        embed = discord.Embed(
            title="Nueva Maqueta para Feedback",
            description=f"**Productor:** {ctx.author.mention}\n**Enlace:** {link}",
            color=discord.Color.purple()
        )
        msg = await ctx.send(embed=embed)
        await msg.create_thread(name=f"Feedback - {ctx.author.name}")
        await ctx.message.delete()

    @commands.command()
    async def share_loops(self, ctx, nombre_pack: str, link: str):
        embed = discord.Embed(
            title="Nuevo Loop Kit Compartido",
            description=f"**Pack:** {nombre_pack}\n**Compartido por:** {ctx.author.mention}\n**Enlace:** {link}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Asegúrate de que sean samples libres de derechos o tipo Static Records.")
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command()
    async def preset_arturia(self, ctx, banco: str, link: str):
        embed = discord.Embed(
            title="Banco de Sonidos Arturia",
            description=f"**Banco:** {banco}\n**Compartido por:** {ctx.author.mention}\n**Enlace:** {link}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command()
    async def collab(self, ctx, rol_buscado: str):
        embed = discord.Embed(
            title="¡Búsqueda de Colaboración!",
            description=f"{ctx.author.mention} está buscando un **{rol_buscado}** para un proyecto.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(ProducerTools(bot))