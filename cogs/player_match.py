
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
GUILD_ID                = int(os.getenv('DISCORD_GUILD_ID'))
RESULTAT_CHANEL_ID      = int(os.getenv('RESULTAT_CHANEL_ID')) 

################################################################################################################
# Modals
################################################################################################################


class BaseInfoModal(Modal):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(title="📝 Partie")
        self.match = match
        self.view = view  # Stocker la référence à la View

        self.status_input = TextInput(
            label="💎 Status",
            placeholder="Choisis dans : " + ", ".join(VALID_STATUSES),
            required=True
        )
        self.winner_input = TextInput(
            label="🏆 Winner",
            placeholder="Choisis le pseudo du joueur",
            required=True
        )
        self.obj_primary_input = TextInput(
            label="🥇 Objectif Primaire",
            placeholder="Choisis l'objectif primaire",
            required=True
        )
        self.obj_secondary_input = TextInput(
            label="🥈 Objectif Secondaire",
            placeholder="Choisis l'objectif secondaire",
            required=True
        )

        self.add_item(self.status_input)
        self.add_item(self.winner_input)
        self.add_item(self.obj_primary_input)
        self.add_item(self.obj_secondary_input)

    async def on_submit(self, interaction: discord.Interaction):

        # VERIFICATION STATUS
        entered_status = self.status_input.value.strip().lower()
        matched_status, score = process.extractOne(entered_status, VALID_STATUSES)

        if score >= SCORE_PROXIMITY :
            self.match.status = matched_status
        else:
            await interaction.response.send_message(
                f"Statut invalide ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_STATUSES)}.",
                ephemeral=True
            )
            return
        
        # VERIFICATION WINNER
        entered_winner =  self.winner_input.value.strip().lower()
        VALID_PSEUDO_PLAYERS = DataManager.get_all_player_pseudos()
        matched_winner, score = process.extractOne(entered_winner, VALID_PSEUDO_PLAYERS)
        
        if score >= SCORE_PROXIMITY :
            self.match.player_winner = matched_winner
        else:
            await interaction.response.send_message(
                f"Player invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_PSEUDO_PLAYERS)}.",
                ephemeral=True
            )
            return
        
        # VERIFICATION OBJ PRIMAIRE
        entered_objective_primary =  self.obj_primary_input.value.strip().lower()
        matched_objective_primary, score = process.extractOne(entered_objective_primary, VALID_OBJECTIVES_PRIMARY)
        
        if score >= SCORE_PROXIMITY-20 :
            self.match.objective_primary = matched_objective_primary
        else:
            await interaction.response.send_message(
                f"Objectif Primaire invalide ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_OBJECTIVES_PRIMARY)}.",
                ephemeral=True
            )
            return       
        
        # VERIFICATION OBJ SECONDAIRE
        entered_objective_secondary =  self.obj_secondary_input.value.strip().lower()
        matched_objective_secondary, score = process.extractOne(entered_objective_secondary, VALID_OBJECTIVES_SECONDARY)
        
        if score >= SCORE_PROXIMITY-20 :
            self.match.objective_secondary = matched_objective_secondary
        else:
            await interaction.response.send_message(
                f"Objectif Secondaire ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_OBJECTIVES_SECONDARY)}.",
                ephemeral=True
            )
            return          


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


        # VERIFICATION PSEUDO
        entered_blue_player_pseudo =  self.pseudo_input.value.strip().lower()
        VALID_PSEUDO_PLAYERS = DataManager.get_all_player_pseudos()
        matched_blue_player_pseudo, score = process.extractOne(entered_blue_player_pseudo, VALID_PSEUDO_PLAYERS)
        
        if score >= SCORE_PROXIMITY :
            self.match.player_blue = matched_blue_player_pseudo
        else:
            await interaction.response.send_message(
                f"Player invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_PSEUDO_PLAYERS)}.",
                ephemeral=True
            )
            return
        

        # VERIFICATION AVANTAGE
        entered_blue_player_avantage =  self.avantage_input.value.strip().lower()
        matched_blue_player_avantage, score = process.extractOne(entered_blue_player_avantage, VALID_ADVANTAGES)
        
        if score >= SCORE_PROXIMITY :
            self.match.avantage_blue = matched_blue_player_avantage
        else:
            await interaction.response.send_message(
                f"Advantage invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_ADVANTAGES)}.",
                ephemeral=True
            )
            return
        
        # VERIFICATION VP_BLUE ET KP_BLUE
        entered_vp_blue = self.vp_input.value.strip()
        entered_kp_blue = self.kp_input.value.strip()

        try:
            vp_blue = int(entered_vp_blue)
            kp_blue = int(entered_kp_blue)
            self.match.vp_blue = vp_blue
            self.match.kp_blue = kp_blue
        except ValueError:
            await interaction.response.send_message(
                "**Erreur :** Les Victory Points (VP) et Kill Points (KP) doivent être des nombres entiers.",
                ephemeral=True
            )
            return


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

       
        # VERIFICATION PSEUDO
        entered_red_player_pseudo =  self.pseudo_input.value.strip().lower()
        VALID_PSEUDO_PLAYERS = DataManager.get_all_player_pseudos()
        matched_red_player_pseudo, score = process.extractOne(entered_red_player_pseudo, VALID_PSEUDO_PLAYERS)
        
        if score >= SCORE_PROXIMITY :
            self.match.player_red = matched_red_player_pseudo
        else:
            await interaction.response.send_message(
                f"Player invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_PSEUDO_PLAYERS)}.",
                ephemeral=True
            )
            return
        

        # VERIFICATION AVANTAGE
        entered_red_player_avantage =  self.avantage_input.value.strip().lower()
        matched_red_player_avantage, score = process.extractOne(entered_red_player_avantage, VALID_ADVANTAGES)
        
        if score >= SCORE_PROXIMITY :
            self.match.avantage_red = matched_red_player_avantage
        else:
            await interaction.response.send_message(
                f"Advantage invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_ADVANTAGES)}.",
                ephemeral=True
            )
            return
        
        # VERIFICATION VP_RED ET KP_RED
        entered_vp_red = self.vp_input.value.strip()
        entered_kp_red = self.kp_input.value.strip()

        try:
            vp_red = int(entered_vp_red)
            kp_red = int(entered_kp_red)
            self.match.vp_red = vp_red
            self.match.kp_red = kp_red
        except ValueError:
            await interaction.response.send_message(
                "**Erreur :** Les Victory Points (VP) et Kill Points (KP) doivent être des nombres entiers.",
                ephemeral=True
            )
            return


        self.match.player_red        = self.pseudo_input.value
        self.match.avantage_red      = self.avantage_input.value
        self.match.vp_red            = self.vp_input.value
        self.match.kp_red            = self.kp_input.value


        if isinstance(self.view, MatchInfoView):
            self.view.red_player_button.label        = "✅"
            self.view.red_player_button.style        = ButtonStyle.success
            self.view.red_player_button.disabled     = True

            await interaction.response.edit_message(view=self.view)


################################################################################################################
# Embed
################################################################################################################



def get_open_matches_embed(matches: list[Match]) -> discord.Embed:
    embed = discord.Embed(title="Résultats des derniers Matchs",
                          colour=0x2b2d31)
    
    for match in matches:
        if match.color_winner and match.color_winner.lower() == "blue":
            embed.add_field(
                name      = "🎡 Poule",
                value     = f"🔵 ` {match.player_blue} 🎖️{match.kp_blue} ` 🏆 ⚔️ ` {match.kp_red}🎖️ {match.player_red} `🔴",
                inline=False
            )
        elif match.color_winner and match.color_winner.lower() == "red":
            embed.add_field(
                name      = "🎡 Poule",
                value     = f"🔵 ` {match.player_blue} 🎖️{match.kp_blue} ` ⚔️ 🏆 ` {match.kp_red}🎖️ {match.player_red} ` 🔴",
                inline=False
            )
        else:
            embed.add_field(
                name      = "🎡 Poule",
                value     = f"` {match.player_blue} ` ⚔️ ` {match.player_red} `",
                inline=False
            )

    if not embed.fields:
        embed.add_field(name="❌ Aucun match ouvert enregistré", value="", inline=False)

    return embed

################################################################################################################
# Views
################################################################################################################


class LatestMatchesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.data_manager = DataManager()

    async def on_timeout(self):
        # Optional: Handle timeout if needed
        pass

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

################################################################################################################
# Button
################################################################################################################

class BaseInfoButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="📝 Partie", style=ButtonStyle.secondary)
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
        super().__init__(label="🔴 Player", style=ButtonStyle.secondary)
        self.match = match

    async def callback(self, interaction: discord.Interaction):
        modal = RedPlayerModal(self.match, self.view)
        await interaction.response.send_modal(modal)

class ValidateButton(Button):
    def __init__(self, match: Match, view: discord.ui.View):
        super().__init__(label="Valider et Enregistrer", style=ButtonStyle.success)
        self.match = match

    async def callback(self, interaction: discord.Interaction):
        
        db = SessionLocal()
        try:
            
            if self.match.status == "poule":
                ligue_blue , poule_blue = DataManager.get_league_and_group_by_pseudo(self.match.player_blue)
                ligue_rouge , poule_red = DataManager.get_league_and_group_by_pseudo(self.match.player_blue)
                if ligue_blue == ligue_rouge and poule_blue == poule_red:
                    ligue_entered = ligue_blue
                    poule_entered = ligue_rouge
                else : 
                    await interaction.response.send_message(
                        f"Une erreur s'est produite lors de l'enregistrement du match : {e}\n Les deux joueurs ne sont pas dans la meme ligue pour un match de poule",
                        ephemeral=True
                    )
            else : 
                ligue_entered = ""
                poule_entered = ""
    

          
            if self.match.player_blue == self.match.player_winner :
                color_winner_entered = "blue"
            elif self.match.player_red == self.match.player_winner :
                color_winner_entered = "red"
            else : 
                color_winner_entered = ""
            

            new_match = Match(
                status                 = self.match.status,
                ligue_entered          = ligue_entered,
                poule                  = poule_entered,
                player_blue            = self.match.player_blue,
                player_red             = self.match.player_red,
                player_winner          = self.match.player_winner,
                color_winner           = color_winner_entered,
                vp_blue                = int(self.match.vp_blue),
                vp_red                 = int(self.match.vp_red),
                objective_primary      = self.match.objective_primary,
                objective_secondary    = self.match.objective_secondary,
                avantage_blue          = self.match.avantage_blue,
                avantage_red           = self.match.avantage_red,
                kp_blue                = int(self.match.kp_blue),
                kp_red                 = int(self.match.kp_red)
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

        # Obtenir le canal de résultats
        resultat_channel = interaction.client.get_channel(RESULTAT_CHANEL_ID)
        if resultat_channel is None:
            logging.error(f"Channel with ID {RESULTAT_CHANEL_ID} not found.")
            return

        # Créer un embed avec les détails du match
        embed = discord.Embed(
            title="Nouveau Match Enregistré",
            description=f"**{new_match.player_blue}** vs **{new_match.player_red}**",
            color=discord.Color.green(),
            timestamp=new_match.created_at
        )
        embed.add_field(name="Statut", value=new_match.status, inline=True)
        embed.add_field(name="Ligue", value=new_match.ligue, inline=True)
        embed.add_field(name="Poule", value=new_match.poule, inline=True)
        embed.add_field(name="Gagnant", value=new_match.player_winner or "N/A", inline=True)
        embed.add_field(name="Couleur Gagnant", value=new_match.color_winner or "N/A", inline=True)
        embed.add_field(name="VP Bleu", value=new_match.vp_blue, inline=True)
        embed.add_field(name="VP Rouge", value=new_match.vp_red, inline=True)
        embed.add_field(name="KP Bleu", value=new_match.kp_blue, inline=True)
        embed.add_field(name="KP Rouge", value=new_match.kp_red, inline=True)
        embed.add_field(name="Objectif Primaire", value=new_match.objective_primary, inline=False)
        embed.add_field(name="Objectif Secondaire", value=new_match.objective_secondary, inline=False)
        embed.add_field(name="Avantage Bleu", value=new_match.avantage_blue, inline=True)
        embed.add_field(name="Avantage Rouge", value=new_match.avantage_red, inline=True)

        # Envoyer l'embed dans le canal de résultats
        try:
            await resultat_channel.send(embed=embed)
        except Exception as e:
            logging.error(f"Failed to send message to channel {RESULTAT_CHANEL_ID}: {e}")


################################################################################################################
# Commande
################################################################################################################

class PlayerMatch(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ajouter_match", 
                          description="Ajouter un nouveau match")
    @app_commands.guilds(GUILD_ID)

    async def ajouter_match_command(self, interaction: discord.Interaction):
        new_match = Match()  
        view = MatchInfoView(new_match)  
        last_matches = DataManager.load_latest_matches(limit=3)  
        embed = get_open_matches_embed(last_matches)
        await interaction.response.send_message(
            "Ajoutez un match",
            embed=embed,  
            view=view,
            ephemeral=True
        )


async def setup(bot: commands.bot.Bot):
    await bot.add_cog(PlayerMatch(bot))
