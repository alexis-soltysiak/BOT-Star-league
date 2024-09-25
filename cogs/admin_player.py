import discord
from discord import app_commands, ButtonStyle
from discord.ext import commands
from discord.ui import Modal, TextInput

from data_manager import DataManager, Player 
import os
from dotenv import load_dotenv
from bdd.db_config import SessionLocal 
import logging
from bdd.models import Admin


from variables import * 
from thefuzz import process 

from help.help_functions import *

# Charger les variables d'environnement
load_dotenv()
GUILD_ID           = int(os.getenv('DISCORD_GUILD_ID'))
RESULTAT_CHANEL_ID = int(os.getenv('RESULTAT_CHANEL_ID'))  



# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




################################################################################################################
# Modals
################################################################################################################

class AddPlayerModal(Modal):
    """
    Modal pour ajouter un nouveau joueur.
    Collecte les informations suivantes :
    - Pseudo
    - Ligue
    - Poule
    - Faction
    - Liste
    """

    def __init__(self):
        super().__init__(title="Ajouter un nouveau joueur")

        # Champ pour le pseudo
        self.pseudo_input = TextInput(
            label="Pseudo",
            placeholder="Entrez le pseudo du joueur",
            required=True,
            max_length=32
        )
        # Champ pour la ligue
        self.ligue_input = TextInput(
            label="Ligue",
            placeholder="Entrez la ligue du joueur",
            required=True,
            max_length=32
        )
        # Champ pour la poule
        self.poule_input = TextInput(
            label="Poule",
            placeholder="Entrez la poule du joueur",
            required=True,
            max_length=32
        )
        # Champ pour la faction
        self.faction_input = TextInput(
            label="Faction",
            placeholder="Entrez la faction du joueur",
            required=True,
            max_length=32
        )
        # Champ pour la liste
        self.liste_input = TextInput(
            label="Liste",
            placeholder="Entrez la liste du joueur",
            required=True,
            max_length=512
        )

        # Ajouter les champs au modal
        self.add_item(self.pseudo_input)
        self.add_item(self.ligue_input)
        self.add_item(self.poule_input)
        self.add_item(self.faction_input)
        self.add_item(self.liste_input)

    async def on_submit(self, interaction: discord.Interaction):

        pseudo = self.pseudo_input.value.strip()
        ligue = self.ligue_input.value.strip()
        poule = self.poule_input.value.strip()
        faction = self.faction_input.value.strip()
        liste = self.liste_input.value.strip()

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "Impossible de récupérer les informations du serveur.",
                ephemeral=True
            )
            return

        # Collecter tous les noms d'utilisateur des membres
        member_names = [member.name for member in guild.members]  # Utiliser seulement le nom d'utilisateur

        # Utiliser thefuzz pour trouver le nom d'utilisateur le plus proche
        matched_username, score = process.extractOne(pseudo, member_names)

        if score < SCORE_PROXIMITY:
            await interaction.response.send_message(
                f"Aucun membre avec un nom d'utilisateur proche de `{pseudo}` trouvé dans ce serveur. Veuillez vérifier le nom d'utilisateur et réessayer.",
                ephemeral=True
            )
            return

        # Trouver le membre correspondant au nom d'utilisateur trouvé
        member = discord.utils.find(lambda m: m.name == matched_username, guild.members)

        if not member:
            await interaction.response.send_message(
                f"Aucun membre avec le nom d'utilisateur `{matched_username}` trouvé dans ce serveur. Veuillez vérifier le nom d'utilisateur et réessayer.",
                ephemeral=True
            )
            return

        pseudo = matched_username 
        # VERIFICATION LIGUE
        entered_ligue =  ligue.lower()
        matched_ligue, score = process.extractOne(entered_ligue, VALID_LIGUES)
        
        if score >= SCORE_PROXIMITY :
            ligue = matched_ligue
        else:
            await interaction.response.send_message(
                f"Ligue invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_LIGUES)}.",
                ephemeral=True
            )
            return


        # VERIFICATION  POULE
        entered_poule =  poule.lower()
        matched_poule, score = process.extractOne(entered_poule, VALID_POULES)
        
        if score >= SCORE_PROXIMITY :
            poule = matched_poule
        else:
            await interaction.response.send_message(
                f"Poule invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_POULES)}.",
                ephemeral=True
            )
            return
        

        # VERIFICATION  FACTION
        entered_faction =  faction.lower()
        matched_faction, score = process.extractOne(entered_faction, VALID_FACTIONS)
        
        if score >= SCORE_PROXIMITY - 30:
            faction = matched_faction
        else:
            await interaction.response.send_message(
                f"Faction invalid ou non reconnu. Veuillez entrer un statut valide comme : {', '.join(VALID_FACTIONS)}.",
                ephemeral=True
            )
            return


        # Récupérer l'ID Discord du membre et définir le display_name
        discord_id = str(member.id)
        display_name = member.display_name
        is_admin = 'false'  # Valeur par défaut, peut être ajustée selon vos besoins



        db = SessionLocal()
        try:

            existing_player = db.query(Player).filter(
                (Player.pseudo == pseudo) | (Player.discord_id == discord_id)
            ).first()
            if existing_player:
                await interaction.response.send_message(
                    "Un joueur avec ce pseudo ou cet ID Discord existe déjà.",
                    ephemeral=True
                )
                return

            if len(liste) > 512:
                await interaction.response.send_message(
                    "La liste fournie est trop longue. Veuillez réduire sa taille à 512 caractères.",
                    ephemeral=True
                )
                return

            # Créer une nouvelle instance de Player
            new_player = Player(
                pseudo=pseudo,
                discord_id=discord_id,
                display_name=member.display_name,
                ligue=ligue,
                poule=poule,
                faction=faction,
                liste=liste,
                is_admin=is_admin
            )
            db.add(new_player)
            db.commit()
            db.refresh(new_player)
        except Exception as e:
            db.rollback()
            logging.error(f"Failed to add new player: {e}")
            await interaction.response.send_message(
                f"Une erreur s'est produite lors de l'ajout du joueur : {e}",
                ephemeral=True
            )
            return
        finally:
            db.close()

        # Créer un embed de confirmation
        embed = discord.Embed(
            title="Nouveau Joueur Ajouté",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="💾 Pseudo", value=new_player.pseudo, inline=True)
        embed.add_field(name="🧬 Discord ID", value=new_player.discord_id, inline=True)
        embed.add_field(name="🔦 Display Name", value=new_player.display_name, inline=True)
        embed.add_field(name="🌍 Ligue", value=new_player.ligue, inline=True)
        embed.add_field(name="🎡 Poule", value=new_player.poule, inline=True)
        embed.add_field(name="⚖️ Faction", value=new_player.faction, inline=True)
        embed.add_field(name="📃 Liste", value=new_player.liste, inline=False)

        # Envoyer l'embed de confirmation à l'utilisateur
        await interaction.response.send_message(
            embed=embed,
            ephemeral=False
        )

################################################################################################################
# Commande
################################################################################################################

class AdminPlayer(commands.Cog):
    """
    Cog pour gérer l'ajout des joueurs.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
                
    @app_commands.command(name="ajouter_joueur", description="Ajouter un nouveau joueur")
    @app_commands.guilds(GUILD_ID)
    async def ajouter_joueur_command(self, interaction: discord.Interaction):
        """
        Commande pour ajouter un nouveau joueur.
        Ouvre le modal pour collecter les informations du joueur.
        """
        if (admin_required(interaction)):
            modal = AddPlayerModal()
            await interaction.response.send_modal(modal)
        else : 
            await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)


################################################################################################################
# Configuration du Cog
################################################################################################################

async def setup(bot: commands.Bot):
    """
    Fonction d'installation du Cog.
    """
    await bot.add_cog(AdminPlayer(bot))




