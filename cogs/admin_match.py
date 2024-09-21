
import discord
from discord import app_commands, ButtonStyle
from discord.ext import commands

from utilities import Utilities
from data_manager import DataManager, Match, Player
import os
from dotenv import load_dotenv
from bdd.db_config import SessionLocal  # Assurez-vous que le chemin est correct
from bdd.models import Admin
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Charger les variables d'environnement
load_dotenv()
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))


class PlayerBuilder:
    def __init__(self):
        self.name = None
        self.elo = None
        self.sexe = None

class AddPlayerButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="+ Ajouter un joueur", style=ButtonStyle.green, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = PlayerAddingView()
        await interaction.response.edit_message(embed=get_player_adding_embed(), view=view)


class PlayersListButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Basculer sur la modification des joueurs", style=ButtonStyle.blurple, row=3)

    async def callback(self, interaction: discord.Interaction):
        view = PlayersListView()
        await interaction.response.edit_message(embeds=get_players_embeds(), view=view)




def get_players_embeds() -> list[discord.Embed]:
    return [get_players_embed("Homme"), get_players_embed("Femme")]


def get_players_embed(sexe: str) -> discord.Embed:
    players = DataManager.load_players()

    embed = discord.Embed(title=f"Joueurs __{sexe.lower()}__ enregistrés",
                          colour=0x2b2d31)

    for player in players:
        if player.sexe == sexe:
            embed.add_field(name=player.name,
                            value=(f"**` ELO:`** {player.elo} elo\n" +
                                   f"**`SEXE:`** {player.sexe}"),
                            inline=True)

    if len(embed.fields) == 0:
        embed.add_field(name=f"❌ Aucun joueur __{sexe.lower()}__ enregistré", value="", inline=False)

    return embed


class MatchView(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(PlayersListButton())



class PlayersListView(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(AddPlayerButton())
        
class PlayerAddingView(discord.ui.View):
    def __init__(self, player: PlayerBuilder = None):
        super().__init__()

        self.player = player if player else PlayerBuilder()



def get_open_matches_embed() -> discord.Embed:

    matches = DataManager.load_matches()
    embed = discord.Embed(title="Results Matchs",
                          colour=0x2b2d31)

    for match in matches:
        
        if match.color_winner == "blue" :
            embed.add_field(name = "🎡 Poule \n",value=f"🔵 " +  f"` {match.player_blue} 🎖️{match.kp_blue} ` ⚔️  ` {match.kp_red}🎖️ " + f"{match.player_red} `",inline=False)
        else : 
            embed.add_field(name = "🎡 Poule \n",value=f"🔴 " +  f"` {match.player_blue} 🎖️{match.kp_blue} ` ⚔️  ` {match.kp_red}🎖️ " + f"{match.player_red} `",inline=False)


    if len(embed.fields) == 0:
        embed.add_field(name="❌ Aucun match ouvert enregistré", value="", inline=False)

    return embed


def get_player_adding_embed(player: PlayerBuilder = None) -> discord.Embed:
    if not player:
        player = PlayerBuilder()

    embed = discord.Embed(title="Création d'un joueur",
                          colour=0x2b2d31)

    embed.add_field(name="Nom",
                    value=f"```{player.name}```" if player.name else "**```Pas encore défini```**",
                    inline=False)

    embed.add_field(name="Elo",
                    value=f"```{player.elo}```" if player.elo else "**```Pas encore défini```**",
                    inline=True)

    embed.add_field(name="Sexe",
                    value=f"```{player.sexe}```" if player.sexe else "**```Pas encore défini```**",
                    inline=True)

    return embed


def admin_required(interaction: discord.Interaction) -> bool:
    cog = interaction.client.get_cog('AdminMatchs')
    if cog is None:
        logger.warning("Cog 'AdminMatchs' non trouvé.")
        return False
    is_admin = cog.is_user_admin(interaction.user.id)
    logger.info(f"Vérification admin pour {interaction.user.id}: {is_admin}")
    return is_admin


        
################################################################################################################
# Admin
################################################################################################################

class AdminMatchs(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_user_admin(self, discord_id: int) -> bool:
        with SessionLocal() as session:
            admin = session.query(Admin).filter_by(discord_id=str(discord_id), is_admin=True).first()
            if admin:
                logger.info(f"Admin trouvé pour l'ID Discord: {discord_id}")
                return True
            else:
                logger.info(f"Aucun admin trouvé pour l'ID Discord: {discord_id}")
                return False
            
    @app_commands.command(
        name="admin_match",
        description="Afficher le panneau de management des pronostics, des matches et des joueurs"
    )
    @app_commands.guilds(GUILD_ID)
    async def prono_admin_pannel(self, interaction: discord.Interaction):
        """Commande /prono-admin réservée aux administrateurs."""
        if (admin_required(interaction)):
            view = MatchView()
            embed = get_open_matches_embed()
            await interaction.response.send_message(embed=embed, view=view)
        else : 
            await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)


async def setup(bot: commands.bot.Bot):
    await bot.add_cog(AdminMatchs(bot))
