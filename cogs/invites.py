import discord
from discord.ext import commands
from discord import app_commands

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites: dict[int, list[discord.Invite]] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        try:
            self.invites[invite.guild.id] = await invite.guild.invites()
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        try:
            self.invites[invite.guild.id] = await invite.guild.invites()
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            invites_before = self.invites.get(member.guild.id, [])
            invites_after = await member.guild.invites()
            used_invite = None
            for invite in invites_before:
                found = discord.utils.get(invites_after, code=invite.code)
                if found and found.uses > invite.uses:
                    used_invite = invite
                    break
            if used_invite and used_invite.inviter:
                async with self.bot.db_pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO invites (joined_id, inviter_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                        member.id, used_invite.inviter.id
                    )
            self.invites[member.guild.id] = invites_after
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            async with self.bot.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM invites WHERE joined_id = $1", member.id)
        except Exception:
            pass

    @app_commands.command(name="invitaciones", description="Muestra cuántas personas ha invitado un usuario")
    async def invitaciones(self, interaction: discord.Interaction, usuario: discord.Member = None):
        user = usuario or interaction.user
        async with self.bot.db_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM invites WHERE inviter_id = $1", user.id)

        embed = discord.Embed(title="🔗 Contador de Invitaciones", color=discord.Color.purple())
        embed.add_field(name="Usuario", value=user.mention, inline=True)
        embed.add_field(name="Invitaciones activas", value=f"**{count}**", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))