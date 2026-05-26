import discord
from discord.ext import commands
import chat_exporter
import io

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Soporte General", description="Problemas con el servidor o dudas", emoji="🛠️"),
            discord.SelectOption(label="Negocios / Collab", description="Propuestas comerciales o proyectos", emoji="💼"),
            discord.SelectOption(label="Revisión Privada", description="Enviar track directo al staff", emoji="🎧")
        ]
        super().__init__(placeholder="Selecciona el tipo de ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        
        if not category:
            category = await guild.create_category("TICKETS")

        tipo = self.values[0].split()[0].lower()
        channel = await guild.create_text_channel(
            name=f"{tipo}-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
            }
        )

        embed = discord.Embed(
            title=f"Ticket: {self.values[0]}", 
            description=f"Hola {interaction.user.mention}, describe tu solicitud aquí. El staff te atenderá en breve.", 
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket creado correctamente en {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar y Guardar Transcript", style=discord.ButtonStyle.danger, custom_id="cerrar_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{interaction.channel.name}.html")
            try:
                await interaction.user.send("Respaldo de tu ticket:", file=transcript_file)
            except discord.Forbidden:
                pass
                
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel_tickets")
    @commands.has_permissions(administrator=True)
    async def panel_tickets(self, ctx):
        embed = discord.Embed(
            title="Centro de Soporte y Contacto", 
            description="Selecciona en el menú desplegable de abajo el tipo de ticket que deseas abrir.", 
            color=discord.Color.dark_theme()
        )
        await ctx.send(embed=embed, view=TicketView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))