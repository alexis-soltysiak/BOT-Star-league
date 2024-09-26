# classement_progression.py

import discord
from discord import app_commands
from discord.ext import commands
from data_manager import DataManager
import os
from dotenv import load_dotenv
from typing import List, Dict
from variables import DICT_EMOJI_LIGUES_DISPLAY,VALID_LIGUES  # Assurez-vous que cette variable est définie
from help.help_functions import *


# Charger les variables d'environnement
load_dotenv()
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

class ClassementProgression(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="progression", description="Afficher la progression des poules par ligue")
    @app_commands.guilds(GUILD_ID)
    async def classement_progression_command(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=False)

        if (admin_required(interaction)):
                
            # Récupérer toutes les ligues
            ligues = VALID_LIGUES

            if not ligues:
                await interaction.followup.send("Aucune ligue trouvée.", ephemeral=True)
                return


            description = ""

            for ligue in ligues:
                # Récupérer les poules de la ligue
                poules = DataManager.get_poules_by_league(ligue)

                if not poules:
                    continue  # Passer à la ligue suivante si aucune poule trouvée

                # Trier les poules par ordre alphabétique
                poules_sorted = sorted(poules)

                # Initialiser le contenu pour cette ligue
                ligue_header = f"Ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}\n"

                # Initialiser le bloc de code pour cette ligue
                code_block = f"```\n{ligue_header}"

                for poule in poules_sorted:
                    # Calculer le nombre de matchs joués pour la poule
                    matches_played = DataManager.get_matches_played_count(ligue, poule)
                    max_matches = 6
                    progress = min(matches_played, max_matches)  # S'assurer que le nombre ne dépasse pas le maximum

                    # Générer la barre de progression
                    progress_bar = self.generate_progress_bar(progress, max_matches)

                    # Ajouter les informations de la poule dans le bloc de code
                    code_block += f"Poule {poule.upper()}\nProgression : {progress_bar} {progress}/{max_matches} matchs\n\n"

                code_block += "```"

                # Ajouter le bloc de code à la description
                description += code_block + "\n\n"

            if not description.strip():
                await interaction.followup.send("Aucune progression trouvée pour les ligues disponibles.", ephemeral=True)
                return

            # Créer l'embed unique
            embed = discord.Embed(
                title="Progression des Poules par Ligue",
                description=description,
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )

            await interaction.followup.send(embed=embed, ephemeral=False)
        else : 
            await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)

    def generate_progress_bar(self, current: int, maximum: int) -> str:
        """
        Génère une barre de progression ASCII.

        Args:
            current (int): Nombre actuel de matchs joués.
            maximum (int): Nombre maximum de matchs.

        Returns:
            str: Barre de progression formatée.
        """
        filled_char = '█'
        empty_char = '░'
        bar = filled_char * current + empty_char * (maximum - current)
        return f"[{bar}]"

async def setup(bot: commands.Bot):
    await bot.add_cog(ClassementProgression(bot))
