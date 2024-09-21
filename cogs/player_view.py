# cogs/player_views.py

import discord
from discord import app_commands, ButtonStyle
from discord.ext import commands
from data_manager import DataManager
from bdd.models import Player  # Assurez-vous que le chemin est correct
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

class PlayerAdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="player-admin", description="Afficher le panneau de gestion des joueurs")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guilds(GUILD_ID)  # Spécifier la guilde pour une synchronisation rapide
    async def player_admin_command(self, interaction: discord.Interaction):
        print("Commande /player-admin invoquée.")
        players = DataManager.load_players()
        print(f"Nombre de joueurs récupérés: {len(players)}")
        if not players:
            await interaction.response.send_message("Aucun joueur trouvé dans la base de données.", ephemeral=True)
            return

        # Trier les joueurs par pseudo ou tout autre critère
        players = sorted(players, key=lambda p: p.pseudo.lower())
        print("Joueurs triés.")

        # Définir le nombre de joueurs par page
        per_page = 10
        total_pages = (len(players) - 1) // per_page + 1
        print(f"Total pages: {total_pages}")

        # Initialiser la première page
        page_number = 1

        # Créer l'embed pour la première page
        embed = self.create_player_embed(players, page_number, per_page, total_pages)
        print("Embed créé pour la première page.")

        # Créer la vue avec les boutons de navigation et d'ajout
        view = PlayersListView(players, per_page, total_pages, page_number)
        print("Vue PlayersListView créée.")

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        print("Message envoyé avec embed et vue.")

    def create_player_embed(self, players, page_number, per_page, total_pages):
        embed = discord.Embed(
            title="Liste des Joueurs",
            color=discord.Color.blue(),
            description=f"Page {page_number} sur {total_pages}"
        )

        start = (page_number - 1) * per_page
        end = start + per_page
        for player in players[start:end]:
            embed.add_field(
                name=player.pseudo,
                value=f"Discord ID: {player.discord_id}\nNom Affiché: {player.display_name}\nLigue: {player.ligue}\nPoule: {player.poule}\nArmée: {player.armee}\nListe: {player.liste}\nAdmin: {player.is_admin}",
                inline=False
            )

        return embed

class PlayersListView(discord.ui.View):
    def __init__(self, players, per_page, total_pages, current_page):
        super().__init__(timeout=180)  # Vue active pendant 3 minutes
        self.players = players
        self.per_page = per_page
        self.total_pages = total_pages
        self.current_page = current_page

        # Ajouter les boutons de pagination
        self.add_item(PreviousPageButton(self))
        self.add_item(NextPageButton(self))
        # Ajouter le bouton "Ajouter un Joueur"
        self.add_item(AddPlayerButton(self))

    def create_embed(self):
        embed = discord.Embed(
            title="Liste des Joueurs",
            color=discord.Color.blue(),
            description=f"Page {self.current_page} sur {self.total_pages}"
        )

        start = (self.current_page - 1) * self.per_page
        end = start + self.per_page
        for player in self.players[start:end]:
            embed.add_field(
                name=player.pseudo,
                value=f"Discord ID: {player.discord_id}\nNom Affiché: {player.display_name}\nLigue: {player.ligue}\nPoule: {player.poule}\nArmée: {player.armee}\nListe: {player.liste}\nAdmin: {player.is_admin}",
                inline=False
            )

        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class PreviousPageButton(discord.ui.Button):
    def __init__(self, parent_view: PlayersListView):
        super().__init__(label="⬅️ Précédent", style=ButtonStyle.primary)
        self.parent_view = parent_view  # Utilisez un autre nom d'attribut

    async def callback(self, interaction: discord.Interaction):
        print("Bouton 'Précédent' cliqué.")
        if self.parent_view.current_page > 1:
            self.parent_view.current_page -= 1
            print(f"Passage à la page {self.parent_view.current_page}.")
            await self.parent_view.update_message(interaction)
        else:
            print("Déjà sur la première page.")
            await interaction.response.send_message("Vous êtes déjà sur la première page.", ephemeral=True)

class NextPageButton(discord.ui.Button):
    def __init__(self, parent_view: PlayersListView):
        super().__init__(label="Suivant ➡️", style=ButtonStyle.primary)
        self.parent_view = parent_view  # Utilisez un autre nom d'attribut

    async def callback(self, interaction: discord.Interaction):
        print("Bouton 'Suivant' cliqué.")
        if self.parent_view.current_page < self.parent_view.total_pages:
            self.parent_view.current_page += 1
            print(f"Passage à la page {self.parent_view.current_page}.")
            await self.parent_view.update_message(interaction)
        else:
            print("Déjà sur la dernière page.")
            await interaction.response.send_message("Vous êtes déjà sur la dernière page.", ephemeral=True)

class AddPlayerButton(discord.ui.Button):
    def __init__(self, parent_view: PlayersListView):
        super().__init__(label="➕ Ajouter un Joueur", style=ButtonStyle.success)
        self.parent_view = parent_view  # Référence à la vue parent

    async def callback(self, interaction: discord.Interaction):
        print("Bouton 'Ajouter un Joueur' cliqué.")
        modal = AddPlayerModal()
        await interaction.response.send_modal(modal)

class AddPlayerModal(discord.ui.Modal, title="Ajouter un Nouveau Joueur"):
    pseudo = discord.ui.TextInput(label="Pseudo", max_length=32)
    discord_id = discord.ui.TextInput(label="ID Discord", max_length=32)
    display_name = discord.ui.TextInput(label="Nom Affiché", max_length=32)
    ligue = discord.ui.TextInput(label="Ligue", max_length=32)
    poule = discord.ui.TextInput(label="Poule", max_length=32)
    armee = discord.ui.TextInput(label="Armée", max_length=32)
    liste = discord.ui.TextInput(label="Liste", max_length=32)
    is_admin = discord.ui.TextInput(label="Est Admin (oui/non)", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        # Récupérer les données du modal
        pseudo = self.pseudo.value.strip()
        discord_id = self.discord_id.value.strip()
        display_name = self.display_name.value.strip()
        ligue = self.ligue.value.strip()
        poule = self.poule.value.strip()
        armee = self.armee.value.strip()
        liste = self.liste.value.strip()
        is_admin = self.is_admin.value.strip().lower()

        # Validation de base
        if is_admin not in ["oui", "non"]:
            await interaction.response.send_message("Le champ 'Est Admin' doit être 'oui' ou 'non'.", ephemeral=True)
            return

        # Vérifier si le pseudo ou l'ID Discord existe déjà
        existing_pseudo = DataManager.get_player_info(pseudo)
        existing_discord_id = DataManager.get_player_info_by_iddiscord(discord_id)

        if existing_pseudo:
            await interaction.response.send_message(f"Le pseudo **{pseudo}** est déjà utilisé.", ephemeral=True)
            return

        if existing_discord_id:
            await interaction.response.send_message(f"L'ID Discord **{discord_id}** est déjà utilisé.", ephemeral=True)
            return
 
        # Créer une instance de Player
        new_player = Player(
            pseudo=pseudo,
            discord_id=discord_id,
            display_name=display_name,
            ligue=ligue,
            poule=poule,
            armee=armee,
            liste=liste,
            is_admin=is_admin
        )

        try:
            # Ajouter le joueur à la base de données
            DataManager.add_player(new_player)
            await interaction.response.send_message(f"Joueur **{pseudo}** ajouté avec succès !", ephemeral=True)
            print(f"Joueur ajouté : {pseudo}")

        except Exception as e:
            print(f"Erreur lors de l'ajout du joueur : {e}")
            await interaction.response.send_message("Une erreur est survenue lors de l'ajout du joueur.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerAdminCog(bot))
