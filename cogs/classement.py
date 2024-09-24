# player_player.py

import discord
from discord import app_commands, ButtonStyle
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from thefuzz import process

from data_manager import DataManager, Match, Player
from bdd.db_config import SessionLocal
from bdd.models import Admin

import os
from dotenv import load_dotenv
import logging

from variables import VALID_LIGUES, VALID_FACTIONS, SCORE_PROXIMITY, VALID_STATUSES, VALID_OBJECTIVES_PRIMARY, VALID_OBJECTIVES_SECONDARY, VALID_ADVANTAGES, DICT_EMOJI_LIGUES_DISPLAY

# Charger les variables d'environnement
load_dotenv()
GUILD_ID           = int(os.getenv('DISCORD_GUILD_ID'))
RESULTAT_CHANEL_ID = int(os.getenv('RESULTAT_CHANEL_ID'))

# Chemin vers le dossier des images
MEDIA_PATH = "media"

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

################################################################################################################
# Fonctions Utilitaires
################################################################################################################

def get_matches_by_faction(faction: str) -> list:
    """
    Récupère tous les matchs pour une faction spécifique.
    """
    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.faction == faction).all()
        return matches
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des matchs pour la faction {faction}: {e}")
        return []
    finally:
        db.close()

def get_matches_by_ligue_and_poule(ligue: str) -> dict:
    """
    Récupère tous les matchs pour une ligue spécifique, organisés par poule.
    """
    db = SessionLocal()
    try:
        # Récupérer tous les matchs de la ligue
        matches = db.query(Match).filter(Match.ligue == ligue).all()
        # Organiser les matchs par poule
        matches_by_poule = {}
        for match in matches:
            poule = match.poule
            if poule not in matches_by_poule:
                matches_by_poule[poule] = []
            matches_by_poule[poule].append(match)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des matchs pour la ligue {ligue}: {e}")
        matches_by_poule = {}
    finally:
        db.close()
    return matches_by_poule

def create_combined_matches_embed(matches_by_poule: dict, ligue: str) -> discord.Embed:
    """
    Génère un embed affichant les matchs organisés par poule pour une ligue spécifique.
    """
    embed = discord.Embed(
        title=f"Matchs pour la ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}",
        color=discord.Color.blue()
    )
    if not matches_by_poule:
        embed.description = "Aucun match trouvé pour cette ligue."
    else:
        for poule, matches in matches_by_poule.items():
            value = ""
            for match in matches:
                match_info = (
                    f"**{match.player_blue}** vs **{match.player_red}**\n"
                    f"Vainqueur : {match.player_winner or 'N/A'}\n"
                    f"Status : {match.status}\n"
                    f"VP : {match.vp_blue} - {match.vp_red}\n"
                    f"Date : {match.created_at.strftime('%d/%m/%Y')}\n"
                    "--------------------\n"
                )
                if len(value) + len(match_info) > 1024:
                    # Ajouter le champ et recommencer la valeur
                    embed.add_field(name=f"Poule {poule.capitalize()}", value=value, inline=False)
                    value = match_info
                else:
                    value += match_info
            if value:
                embed.add_field(name=f"Poule {poule.capitalize()}", value=value, inline=False)
    return embed

def calculate_rankings_by_ligue_and_poule(ligue: str) -> dict:
    """
    Calcule le classement des joueurs pour une ligue et poule spécifiques.
    Une victoire = 3 points, égalité = 1 point, défaite = 0 point.
    En cas d'égalité de points, la somme des VP est utilisée comme critère de départage.
    """
    session = SessionLocal()
    try:
        # Récupérer tous les joueurs de la ligue
        players = session.query(Player).filter(Player.ligue == ligue).all()
        # Organiser les joueurs par poule
        players_by_poule = {}
        for player in players:
            poule = player.poule
            if poule not in players_by_poule:
                players_by_poule[poule] = {}
            players_by_poule[poule][player.pseudo] = {
                'points': 0,
                'vp': 0
            }

        # Récupérer tous les matchs de la ligue
        matches = session.query(Match).filter(Match.ligue == ligue).all()

        for match in matches:
            poule = match.poule
            # Vérifier si les joueurs sont dans la poule
            stats_blue = players_by_poule.get(poule, {}).get(match.player_blue)
            stats_red = players_by_poule.get(poule, {}).get(match.player_red)

            # Mettre à jour les VP
            if stats_blue is not None:
                stats_blue['vp'] += match.vp_blue
            if stats_red is not None:
                stats_red['vp'] += match.vp_red

            # Déterminer les points
            if match.player_winner == match.player_blue:
                if stats_blue is not None:
                    stats_blue['points'] += 3
                if stats_red is not None:
                    stats_red['points'] += 0
            elif match.player_winner == match.player_red:
                if stats_red is not None:
                    stats_red['points'] += 3
                if stats_blue is not None:
                    stats_blue['points'] += 0
            else:
                # Match nul
                if stats_blue is not None:
                    stats_blue['points'] += 1
                if stats_red is not None:
                    stats_red['points'] += 1

        # Créer la liste de classement pour chaque poule
        rankings_by_poule = {}
        for poule, players_stats in players_by_poule.items():
            # Convertir en liste et trier par points puis VP
            ranking_list = sorted(
                players_stats.items(),
                key=lambda item: (-item[1]['points'], -item[1]['vp'])
            )
            rankings_by_poule[poule] = ranking_list
    except Exception as e:
        logger.error(f"Erreur lors du calcul du classement pour la ligue {ligue}: {e}")
        rankings_by_poule = {}
    finally:
        session.close()
    return rankings_by_poule

def create_combined_rankings_embed(rankings_by_poule: dict, ligue: str) -> discord.Embed:
    """
    Génère un embed affichant le classement des joueurs organisés par poule pour une ligue spécifique.
    """
    embed = discord.Embed(
        title=f"Classement pour la ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}",
        color=discord.Color.gold()
    )
    if not rankings_by_poule:
        embed.description = "Aucun joueur trouvé pour cette ligue."
    else:
        for poule, ranking_list in rankings_by_poule.items():
            description = ""
            for rank, (pseudo, stats) in enumerate(ranking_list, start=1):
                description += f"{rank}. **{pseudo}** - Points: {stats['points']}, VP: {stats['vp']}\n"
            embed.add_field(name=f"Poule {poule.capitalize()}", value=description, inline=False)
    return embed

################################################################################################################
# Boutons
################################################################################################################

class MatchLigueButton(Button):
    def __init__(self, ligue: str):
        emoji = DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), "")
        super().__init__(label=f"{emoji} Matchs {ligue.capitalize()}", style=ButtonStyle.primary)
        self.ligue = ligue

    async def callback(self, interaction: discord.Interaction):
        matches_by_poule = get_matches_by_ligue_and_poule(self.ligue)
        embed = create_combined_matches_embed(matches_by_poule, self.ligue)
        
        # Chemin vers l'image correspondante
        image_filename = f"{self.ligue}.png"
        image_path = os.path.join(MEDIA_PATH, image_filename)
        
        # Vérifier si le fichier existe
        if os.path.isfile(image_path):
            file = discord.File(image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            await interaction.response.edit_message(embed=embed, view=self.view, attachments=[file])
        else:
            embed.set_footer(text="Image non disponible pour cette ligue.")
            await interaction.response.edit_message(embed=embed, view=self.view)

class RankingLigueButton(Button):
    def __init__(self, ligue: str):
        emoji = DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), "")
        super().__init__(label=f"{emoji} Classement {ligue.capitalize()}", style=ButtonStyle.secondary)
        self.ligue = ligue

    async def callback(self, interaction: discord.Interaction):
        rankings_by_poule = calculate_rankings_by_ligue_and_poule(self.ligue)
        embed = create_combined_rankings_embed(rankings_by_poule, self.ligue)
        
        # Chemin vers l'image correspondante
        image_filename = f"{self.ligue}_classement.png"
        image_path = os.path.join(MEDIA_PATH, image_filename)
        
        # Vérifier si le fichier existe
        if os.path.isfile(image_path):
            file = discord.File(image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            await interaction.response.edit_message(embed=embed, view=self.view, attachments=[file])
        else:
            embed.set_footer(text="Image de classement non disponible pour cette ligue.")
            await interaction.response.edit_message(embed=embed, view=self.view)

################################################################################################################
# Vues
################################################################################################################

class ClassementView(View):
    def __init__(self):
        super().__init__(timeout=180)  # Timeout après 3 minutes

        # Boutons pour afficher les matchs par ligue (première ligne)
        for ligue in VALID_LIGUES:
            button = MatchLigueButton(ligue)
            button.row = 0  # Première ligne
            self.add_item(button)

        # Boutons pour afficher les classements par ligue (deuxième ligne)
        for ligue in VALID_LIGUES:
            button = RankingLigueButton(ligue)
            button.row = 1  # Deuxième ligne
            self.add_item(button)

################################################################################################################
# Cog
################################################################################################################

class PlayerClassement(commands.Cog):
    """
    Cog pour gérer la commande /classement et afficher les classements des ligues.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="classement", description="Afficher les classements")
    @app_commands.guilds(GUILD_ID)
    async def classement_command(self, interaction: discord.Interaction):
        """
        Commande /classement qui affiche des boutons pour chaque ligue.
        """
        view = ClassementView()
        embed = discord.Embed(
            title="Classement des Ligues",
            description="Sélectionnez une ligue pour afficher les matchs ou le classement.",
            colour=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=False  # Peut être True si vous voulez que seul l'utilisateur voit
        )

################################################################################################################
# Configuration du Cog
################################################################################################################

async def setup(bot: commands.Bot):
    """
    Fonction d'installation du Cog.
    """
    await bot.add_cog(PlayerClassement(bot))
