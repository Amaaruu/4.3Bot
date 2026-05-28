import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands")
    @commands.has_permissions(administrator=True)
    async def commands_public(self, ctx):
        embed = discord.Embed(
            title="📋  Comandos de la Comunidad",
            description=(
                "Guía completa de todos los comandos disponibles para productores y artistas.\n"
                "Usa `/` en cualquier canal para acceder a los slash commands.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.from_rgb(138, 43, 226)
        )

        embed.add_field(
            name="🎛️  PRODUCCIÓN",
            value=(
                "`/share_pack` — Comparte un Sample o Loop Pack con la comunidad\n"
                "`/feedback [link] [género]` — Publica tu maqueta y recibe críticas\n"
                "`/beatidea` — Genera un concepto creativo para tu próximo beat\n"
                "`/bpm [género]` — Obtén el BPM ideal para tu estilo musical\n"
                "`/scale [vibe]` — Encuentra la escala perfecta según el mood de tu track"
            ),
            inline=False
        )

        embed.add_field(
            name="🎤  CREATIVIDAD",
            value=(
                "`/lyricsidea` — Inspírate con ideas para escribir letras\n"
                "`/artistname` — Genera un nombre artístico único y original\n"
                "`/songname` — Obtén títulos creativos para tus canciones"
            ),
            inline=False
        )

        embed.add_field(
            name="👤  PERFIL",
            value=(
                "`/perfil [@usuario]` — Visualiza tu perfil musical o el de otro miembro\n"
                "`/editarperfil` — Configura tu DAW, género musical y servicios ofrecidos"
            ),
            inline=False
        )

        embed.add_field(
            name="🌐  COMUNIDAD",
            value=(
                "`/invitaciones [@usuario]` — Consulta tu contador de invitaciones al servidor\n"
                "`🎫  Sistema de Tickets` — Dirígete al canal de tickets para soporte,\n"
                "solicitudes de rango, compras y consultas con el staff"
            ),
            inline=False
        )

        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value=(
                "💡  Para `/scale`, los vibes disponibles son: `triste`, `oscuro`, `feliz`,\n"
                "`epico`, `melancolico`, `misterioso`, `romantico`\n\n"
                "📦  Los packs en `/share_pack` se almacenan en la base de datos del servidor\n"
                "y pueden ser reportados si contienen contenido inapropiado."
            ),
            inline=False
        )

        embed.set_footer(text="Comunidad de Productores & Artistas Emergentes  •  Usa los comandos con responsabilidad")

        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @commands_public.error
    async def commands_public_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

    @commands.command(name="commands_staff")
    @commands.has_permissions(administrator=True)
    async def commands_staff(self, ctx):
        embed = discord.Embed(
            title="⚙️  Panel de Comandos — Staff & Administración",
            description=(
                "Referencia completa de todos los comandos de moderación, configuración y gestión.\n"
                "Este panel es exclusivo para administradores y staff del servidor.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.from_rgb(180, 30, 30)
        )

        embed.add_field(
            name="🔨  MODERACIÓN",
            value=(
                "`/ban [@usuario] [razón]` — Banea permanentemente a un usuario\n"
                "`/kick [@usuario] [razón]` — Expulsa a un usuario del servidor\n"
                "`/timeout [@usuario] [minutos] [razón]` — Silencia temporalmente\n"
                "`/warn [@usuario] [razón]` — Emite una advertencia formal\n"
                "`/unwarn [id]` — Elimina una advertencia por su ID\n"
                "`/warns [@usuario]` — Consulta el historial de advertencias\n"
                "`/lock` — Bloquea el canal actual para usuarios\n"
                "`/unlock` — Desbloquea el canal actual\n"
                "`/clear [cantidad]` — Elimina mensajes en masa (máx. 100)"
            ),
            inline=False
        )

        embed.add_field(
            name="🎫  TICKETS",
            value=(
                "`!panel_tickets` — Despliega el panel de tickets en el canal actual"
            ),
            inline=False
        )

        embed.add_field(
            name="📢  ANUNCIOS & DROPS",
            value=(
                "`/alert` — Envía una alerta oficial con embed personalizado\n"
                "`/newdrop [días] [horas] [minutos]` — Anuncia un drop con contador regresivo"
            ),
            inline=False
        )

        embed.add_field(
            name="👤  GESTIÓN DE PERFILES",
            value=(
                "`/reputacion [@usuario] [add/remove] [cantidad]` — Modifica la reputación\n"
                "`/tracks [@usuario] [add/remove] [cantidad]` — Ajusta el contador de tracks"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️  CONFIGURACIÓN",
            value=(
                "`/setverificacion [banner_url]` — Genera el panel de verificación de miembros\n"
                "`!commands` — Publica el embed de comandos públicos en el canal actual\n"
                "`!commands_staff` — Muestra este panel (solo administradores)"
            ),
            inline=False
        )

        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value=(
                "🔒  El anti-spam automático actúa cuando un usuario supera 5 mensajes en 5 segundos.\n"
                "🔗  El filtro de links permite solo: SoundCloud, Spotify, YouTube,\n"
                "Drive, Mediafire y Mega. El resto es eliminado automáticamente."
            ),
            inline=False
        )

        embed.set_footer(text="Panel restringido  •  Solo accesible por Administradores del servidor")

        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @commands_staff.error
    async def commands_staff_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Help(bot))