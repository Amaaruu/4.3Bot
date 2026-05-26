import discord
from discord.ext import commands
import chat_exporter
import io

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.success, custom_id="abrir_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        
        if not category:
            category = await guild.create_category("TICKETS")

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )

        close_view = CloseTicketView()
        await channel.send(f"Hola {interaction.user.mention}, detalla tu solicitud. Un moderador te atenderá pronto.", view=close_view)
        await interaction.response.send_message(f"Ticket creado en {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar y Exportar", style=discord.ButtonStyle.danger, custom_id="cerrar_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{interaction.channel.name}.html")
            user = interaction.user
            try:
                await user.send("Aquí tienes el respaldo de tu ticket:", file=transcript_file)
            except discord.Forbidden:
                pass

        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        embed = discord.Embed(
            title="Soporte y Contacto", 
            description="Haz clic en el botón para abrir un ticket.", 
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))