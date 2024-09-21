import discord
from discord.ext import commands
from discord import app_commands

from utilities import Utilities


class Misc(commands.Cog):
    def __init__(self, bot: commands.bot.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild


    """
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = discord.utils.get(member.guild.roles, name="Membre")
        if role:
            try:
                await member.add_roles(role)
                print(f"Rôle {role.name} attribué à {member.name}")
            except discord.Forbidden:
                print("Le bot n'a pas les permissions nécessaires pour attribuer ce rôle.")
            except discord.HTTPException as e:
                print(f"Une erreur HTTP s'est produite: {e}")
        else:
            print("Pas de rôle pour 'Membre'")
        
    """
    
    @app_commands.command(name="help",
                          description="Rappelle le nom des commandes disponibles ainsi que leur description")
    async def cmd_help(self, interaction: discord.Interaction):
        with open("help.txt", "r", encoding="utf-8") as f:
            content = f.read()

        await interaction.response.send_message(content=content, ephemeral=True)

    @app_commands.command(name="say", description="Envoie un message avec le bot")
    async def cmd_say(self, interaction: discord.Interaction, content: str, channel_id: str = None,
                      reply_message_id: str = None):
        
        if channel_id is None:
            channel = interaction.channel
        else:
            channel = await self.bot.fetch_channel(int(channel_id))

        if reply_message_id is None:
            await channel.send(content=content)
        else:
            message_to_reply_to = await interaction.channel.fetch_message(int(reply_message_id))
            await message_to_reply_to.reply(content=content)

        await interaction.response.send_message(content=f"`{content}` **envoyé dans <#{channel.id}>**",
                                                ephemeral=True, delete_after=5)

    @app_commands.command(name="mp", description="Envoie un message privé avec le bot")
    async def cmd_mp(self, interaction: discord.Interaction, user_id: str, content: str):
        try:
            user_id = int(user_id.replace(" ", ""))
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            await interaction.response.send_message("L'ID utilisateur est invalide.", ephemeral=True, delete_after=5)
            return

        await user.send(content)

        await interaction.response.send_message(content=f"`{content}` **envoyé à __{user.name}__**",
                                                ephemeral=True, delete_after=5)


    @app_commands.command(name="userinfo", description="Envoie les informations sur un utilisateur")
    async def cmd_user_info(self, interaction: discord.Interaction, member_id: str):
        await interaction.response.defer()

        try:
            member_id = int(member_id.replace(" ", ""))
            member = await self.guild.fetch_member(member_id)
        except ValueError:
            await interaction.response.send_message("L'ID utilisateur est invalide.", ephemeral=True, delete_after=5)
            return

        embed = discord.Embed(
            title=f"Informations sur {member.name}",
            description="_ _",
            color=0x2B2D31
        )

        embed.add_field(name="Nom d'utilisateur", value=f"{member.name} **|**  {member.mention}", inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Rôle le plus élevé", value=member.top_role, inline=False)

        joined_at_formatted = Utilities.format_joined_at(member.joined_at)
        embed.add_field(name="Rejoint le", value=joined_at_formatted, inline=False)

        embed.set_thumbnail(url=member.avatar.url)

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.bot.Bot):
    guild = await bot.fetch_guild(Utilities.get_guild_id())
    await bot.add_cog(Misc(bot, guild))
