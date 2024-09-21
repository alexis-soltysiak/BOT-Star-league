
import discord
from discord import app_commands, ButtonStyle
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

from utilities import Utilities
from data_manager import DataManager, Match, Player
import os
from dotenv import load_dotenv
from bdd.db_config import SessionLocal  # Assurez-vous que le chemin est correct
from bdd.models import Admin
import logging
from thefuzz import process  # Importer la fonction de correspondance


from variables import *

# Charger les variables d'environnement
load_dotenv()
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))



class BaseInfoModal(Modal):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(title="📝 Partie")
        self.match = match
        self.view = view  # Stocker la référence à la View

        self.status_input = TextInput(
            label="💎 Status",
            placeholder="(poule, barrage, quart, demi, finale)",
            required=True
        )
        self.winner_input = TextInput(
            label="🏆 Winner",
            placeholder="Entrez le nom de la ligue",
            required=True
        )
        self.obj_primary_input = TextInput(
            label="🥇 Objectif Primaire",
            placeholder="Entrer le nom de l'objectif primaire",
            required=True
        )
        self.obj_secondary_input = TextInput(
            label="🥈 Objectif Secondaire",
            placeholder="Entrer le nom de l'objectif secondaire",
            required=True
        )

        self.add_item(self.status_input)
        self.add_item(self.winner_input)
        self.add_item(self.obj_primary_input)
        self.add_item(self.obj_secondary_input)

    async def on_submit(self, interaction: discord.Interaction):
        entered_status = self.status_input.value.strip().lower()
        matched_status, score = process.extractOne(entered_status, VALID_STATUSES)

        if score >= 70:
            self.match.status = matched_status
        else:
            await interaction.response.send_message(
                f"Statut invalide ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_STATUSES)}.",
                ephemeral=True
            )
            return

        self.match.player_winner = self.winner_input.value
        self.match.objective_primary = self.obj_primary_input.value
        self.match.objective_secondary = self.obj_secondary_input.value

        if isinstance(self.view, MatchInfoView):
            self.view.base_info_button.label = "✅"
            self.view.base_info_button.style = ButtonStyle.success  
            self.view.base_info_button.disabled = True 

            await interaction.response.edit_message(view=self.view)


class BluePlayerModal(Modal):
    def __init__(self, match: Match,view: discord.ui.View):
        super().__init__(title="🔵 Player Information")
        self.match = match
        self.view = view  

        self.pseudo_input = TextInput(
            label="🔵 Pseudo",
            placeholder="Pseudo du joueur Bleu",
            required=True
        )
        self.avantage_input = TextInput(
            label="🔵 Avantage",
            placeholder="Avantage du joueur Bleu",
            required=True
        )
        self.vp_input = TextInput(
            label="🔵 Victory Point",
            placeholder="Victory Point du joueur Bleu",
            required=True
        )
        self.kp_input = TextInput(
            label="🔵 Kill Point",
            placeholder="Kill point du joueur bleu",
            required=True
        )

        self.add_item(self.pseudo_input)
        self.add_item(self.avantage_input)
        self.add_item(self.vp_input)
        self.add_item(self.kp_input)


    async def on_submit(self, interaction: discord.Interaction):

        self.match.player_blue = self.pseudo_input.value
        self.match.avantage_blue= self.avantage_input.value
        self.match.vp_blue = self.vp_input.value
        self.match.kp_blue = self.kp_input.value


        if isinstance(self.view, MatchInfoView):
            self.view.blue_player_button.label = "✅"
            self.view.blue_player_button.style = ButtonStyle.success
            self.view.blue_player_button.disabled = True

            await interaction.response.edit_message(view=self.view)


class RedPlayerModal(Modal):
    def __init__(self, match: Match,view: discord.ui.View):
        super().__init__(title="🔴 Player Information")
        self.match = match
        self.view = view  

        self.pseudo_input = TextInput(
            label        = "🔴 Pseudo",
            placeholder  = "Pseudo du joueur Bleu",
            required     = True
        )
        self.avantage_input = TextInput(
            label        = "🔴 Avantage",
            placeholder  = "Avantage du joueur Bleu",
            required     = True
        )
        self.vp_input = TextInput(
            label        = "🔴 Victory Point",
            placeholder  = "Victory Point du joueur Bleu",
            required     = True
        )
        self.kp_input = TextInput(
            label        = "🔴 Kill Point",
            placeholder  = "Kill point du joueur bleu",
            required     = True
        )

        self.add_item(self.pseudo_input)
        self.add_item(self.avantage_input)
        self.add_item(self.vp_input)
        self.add_item(self.kp_input)


    async def on_submit(self, interaction: discord.Interaction):

        self.match.player_red        = self.pseudo_input.value
        self.match.avantage_red      = self.avantage_input.value
        self.match.vp_red            = self.vp_input.value
        self.match.kp_red            = self.kp_input.value


        if isinstance(self.view, MatchInfoView):
            self.view.red_player_button.label        = "✅"
            self.view.red_player_button.style        = ButtonStyle.success
            self.view.red_player_button.disabled     = True

            await interaction.response.edit_message(view=self.view)


class MatchInfoView(View):
    def __init__(self, match: Match):
        super().__init__(timeout=None)
        self.match = match

        # Créer les boutons et les stocker en tant qu'attributs
        self.base_info_button         = BaseInfoButton(match, self)
        self.blue_player_button       = BluePlayerInfoButton(match, self)
        self.red_player_button        = RedPlayerInfoButton(match, self)
        self.validate_button          = ValidateButton(match, self)

        # Ajouter les boutons à la View
        self.add_item(self.base_info_button)
        self.add_item(self.blue_player_button)
        self.add_item(self.red_player_button)
        self.add_item(self.validate_button)


class BaseInfoButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="📝 Partie", style=ButtonStyle.primary)
        self.match = match

    async def callback(self, interaction: discord.Interaction):
        modal = BaseInfoModal(self.match, self.view)
        await interaction.response.send_modal(modal)

class BluePlayerInfoButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="🔵 Player", style=ButtonStyle.secondary)
        self.match = match
        self.view_ref = view  # Optionnel

    async def callback(self, interaction: discord.Interaction):
        modal = BluePlayerModal(self.match, self.view)  # Passer la référence de la View
        await interaction.response.send_modal(modal)


class RedPlayerInfoButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="🔴 Player", style=ButtonStyle.success)
        self.match = match

    async def callback(self, interaction: discord.Interaction):
        modal = RedPlayerModal(self.match, self.view)
        await interaction.response.send_modal(modal)

class ValidateButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="Valider et Enregistrer", style=ButtonStyle.danger)
        self.match = match

    async def callback(self, interaction: discord.Interaction):
      


        db = SessionLocal()
        try:
            new_match = Match(
                status=self.match.status,
                ligue="a",
                poule="a",
                player_blue=self.match.player_blue,
                player_red=self.match.player_red,
                player_winner=self.match.player_winner,
                color_winner="a",
                vp_blue=int(self.match.vp_blue),
                vp_red=int(self.match.vp_red),
                objective_primary=self.match.objective_primary,
                objective_secondary=self.match.objective_secondary,
                avantage_blue=self.match.avantage_blue,
                avantage_red=self.match.avantage_red,
                kp_blue=int(self.match.kp_blue),
                kp_red=int(self.match.kp_red)
            )
            db.add(new_match)
            db.commit()
            db.refresh(new_match)
        except Exception as e:
            db.rollback()
            await interaction.response.send_message(
                f"Une erreur s'est produite lors de l'enregistrement du match : {e}",
                ephemeral=True
            )
            return
        finally:
            db.close()

        await interaction.response.send_message("Match enregistré avec succès !", ephemeral=True)


class MatchesListView(discord.ui.View):
    def __init__(self):
        super().__init__()

################################################################################################################
# Admin
################################################################################################################

class PlayerMatch(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

     

    @app_commands.command(name="ajouter_match", 
                          description="Ajouter un nouveau match")
    @app_commands.guilds(GUILD_ID)
    async def ajouter_match_command(self, interaction: discord.Interaction):
        view = MatchInfoView(Match)
        await interaction.response.send_message("Ajoute un match", view=view, ephemeral=True)


async def setup(bot: commands.bot.Bot):
    await bot.add_cog(PlayerMatch(bot))
