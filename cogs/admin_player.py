
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

        



class PlayerModifyingSelect(discord.ui.Select):
    def __init__(self, sexe: str, row: int):
        players = DataManager.load_players()

        options = [discord.SelectOption(label=f"{player.name} ({player.elo})", value=player.name)
                   for player in players
                   if player.sexe == sexe]

        super().__init__(placeholder=f"Choisissez un joueur {sexe.lower()} à modifier...", min_values=1, max_values=1,
                         options=options, row=row)

    async def callback(self, interaction: discord.Interaction):
        selected_player_name = self.values[0]

        player_to_modify = DataManager.get_player_info(selected_player_name)

        modal = PlayerInfoModifyingModal(player_to_modify)
        await interaction.response.send_modal(modal)


        
################################################################################################################
# EMBED
################################################################################################################




def get_open_matches_embed() -> discord.Embed:

    matches = DataManager.load_matches()
    embed = discord.Embed(title="Results Matchs",
                          colour=0x2b2d31)

    for match in matches:
        
        if match.color_winner == "blue" :
            embed.add_field(name = "🎡 Poule\n",value=f"🔵 " +  f"` {match.player_blue} 🎖️{match.kp_blue} ` ⚔️  ` {match.kp_red}🎖️ " + f"{match.player_red} `",inline=False)
        else : 
            embed.add_field(name = "🎡 Poule\n",value=f"🔴 " +  f"` {match.player_blue} 🎖️{match.kp_blue} ` ⚔️  ` {match.kp_red}🎖️ " + f"{match.player_red} `",inline=False)


    if len(embed.fields) == 0:
        embed.add_field(name="❌ Aucun match ouvert enregistré", value="", inline=False)

    return embed



        
################################################################################################################
# VIEW
################################################################################################################


class PlayerView(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(Poule())



        
################################################################################################################
# Admin
################################################################################################################


def admin_required(interaction: discord.Interaction) -> bool:
    cog = interaction.client.get_cog('AdminPlayers')
    if cog is None:
        logger.warning("Cog 'AdminPlayers' non trouvé.")
        return False
    is_admin = cog.is_user_admin(interaction.user.id)
    logger.info(f"Vérification admin pour {interaction.user.id}: {is_admin}")
    return is_admin


        

################################################################################################################
# Admin
################################################################################################################

class AdminPlayers(commands.Cog):

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
        name="admin_player",
        description="Afficher le panneau de management des pronostics, des matches et des joueurs"
    )
    @app_commands.guilds(GUILD_ID)
    async def prono_admin_pannel(self, interaction: discord.Interaction):
        """Commande /prono-admin réservée aux administrateurs."""
        if (admin_required(interaction)):
            view = PlayerView()
            embed = get_list_player()
            await interaction.response.send_message(embed=embed, view=view)
        else : 
            await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)


async def setup(bot: commands.bot.Bot):
    await bot.add_cog(AdminPlayers(bot))
