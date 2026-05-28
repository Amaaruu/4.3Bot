import discord
from discord.ext import commands

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild) -> discord.TextChannel:
        channel = discord.utils.get(guild.text_channels, name="logs")
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel = await guild.create_text_channel("logs", overwrites=overwrites)
        return channel

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.guild is None or before.content == after.content:
            return
        channel = await self.get_log_channel(before.guild)
        embed = discord.Embed(title="✏️ Mensaje Editado", color=discord.Color.orange())
        embed.add_field(name="Autor", value=f"{before.author.mention} (`{before.author.id}`)", inline=False)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content[:1020] or "*(vacío)*", inline=False)
        embed.add_field(name="Después", value=after.content[:1020] or "*(vacío)*", inline=False)
        embed.add_field(name="Link", value=f"[Ir al mensaje]({after.jump_url})", inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or message.guild is None:
            return
        channel = await self.get_log_channel(message.guild)
        embed = discord.Embed(title="🗑️ Mensaje Eliminado", color=discord.Color.red())
        embed.add_field(name="Autor", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenido", value=message.content[:1020] or "*(sin texto / adjunto)*", inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_log_channel(member.guild)
        embed = discord.Embed(title="📥 Nuevo Miembro", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Usuario", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="Cuenta creada", value=discord.utils.format_dt(member.created_at, style='R'), inline=True)
        embed.set_footer(text=f"Total miembros: {member.guild.member_count}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.get_log_channel(member.guild)
        embed = discord.Embed(title="📤 Miembro Salió", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Usuario", value=f"{member} (`{member.id}`)", inline=False)
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "Ninguno", inline=False)
        embed.set_footer(text=f"Total miembros: {member.guild.member_count} • {discord.utils.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = await self.get_log_channel(guild)
        embed = discord.Embed(title="🔨 Miembro Baneado", color=discord.Color.dark_red())
        embed.add_field(name="Usuario", value=f"{user} (`{user.id}`)", inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = await self.get_log_channel(guild)
        embed = discord.Embed(title="✅ Miembro Desbaneado", color=discord.Color.green())
        embed.add_field(name="Usuario", value=f"{user} (`{user.id}`)", inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        channel = await self.get_log_channel(invite.guild)
        embed = discord.Embed(title="🔗 Invitación Creada", color=discord.Color.blue())
        embed.add_field(name="Creador", value=invite.inviter.mention if invite.inviter else "Desconocido", inline=True)
        embed.add_field(name="Código", value=f"`{invite.code}`", inline=True)
        embed.add_field(name="Canal", value=invite.channel.mention, inline=True)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        channel = await self.get_log_channel(role.guild)
        embed = discord.Embed(title="🏷️ Rol Creado", color=discord.Color.green())
        embed.add_field(name="Nombre", value=role.mention, inline=True)
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        channel = await self.get_log_channel(role.guild)
        embed = discord.Embed(title="🗑️ Rol Eliminado", color=discord.Color.dark_red())
        embed.add_field(name="Nombre", value=role.name, inline=True)
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.set_footer(text=discord.utils.utcnow().strftime("%d/%m/%Y %H:%M UTC"))
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))