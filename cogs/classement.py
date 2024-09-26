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
from help.help_functions import *

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
        super().__init__(label=f"{emoji} Ranking {ligue.capitalize()}", style=ButtonStyle.secondary)
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

        # Boutons pour afficher les classements par l/igue (deuxième ligne)
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
