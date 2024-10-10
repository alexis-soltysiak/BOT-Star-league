# stats_cog.py

import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import seaborn as sns  # Importer Seaborn
import os
import io
from bdd.db_config import SessionLocal
from bdd.models import Match, Player
from variables import (
    VALID_OBJECTIVES_PRIMARY,
    VALID_OBJECTIVES_SECONDARY,
    VALID_ADVANTAGES,
    VALID_FACTIONS
)
from dotenv import load_dotenv
import logging
import asyncio

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurer Matplotlib pour utiliser le style Seaborn
sns.set_style('darkgrid')  # Utiliser le style Seaborn

class StatsCog(commands.Cog):
    """
    Cog pour gérer les statistiques et générer des graphiques.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Générer et afficher des statistiques graphiques")
    @app_commands.guilds(int(os.getenv('DISCORD_GUILD_ID')))
    async def stats_command(self, interaction: discord.Interaction):
        """
        Commande /stats qui génère des graphiques basés sur les données des matchs et les envoie sur Discord.
        """
        # Envoyer un message initial de chargement
        loading_embed = discord.Embed(
            title="Statistiques des Matchs",
            description="En cours de génération des graphiques...",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=False)

        session: Session = SessionLocal()
        try:
            # Récupérer tous les matchs terminés
            matches = session.query(Match).all()

            if not matches:
                await interaction.followup.send("Aucun match terminé disponible pour générer des statistiques.")
                return

            # Générer les graphiques de manière asynchrone
            charts = await self.generate_charts_async(session, matches)

            if not charts:
                await interaction.followup.send("Aucune statistique disponible à afficher.")
                return

            # Envoyer les graphiques un par un
            for chart_name, chart_image in charts.items():
                embed = discord.Embed(
                    title=chart_name.replace('_', ' ').title(),
                    color=discord.Color.blue()
                )
                embed.set_image(url=f"attachment://{chart_name}.png")

                # Créer un fichier discord.File à partir de BytesIO
                file = discord.File(chart_image, filename=f"{chart_name}.png")

                await interaction.followup.send(embed=embed, file=file)
                await asyncio.sleep(1)  # Pause d'une seconde entre les envois pour éviter les limites de taux

        except Exception as e:
            logger.error(f"Erreur lors de la génération des statistiques: {e}")
            await interaction.followup.send("Une erreur est survenue lors de la génération des statistiques.")
        finally:
            session.close()

    async def generate_charts_async(self, session: Session, matches):
        """
        Génère les graphiques requis de manière asynchrone et les enregistre dans des objets BytesIO.

        Retourne un dictionnaire avec le nom du graphique comme clé et l'objet BytesIO comme valeur.
        """
        charts = {}
        loop = asyncio.get_event_loop()

        try:
            # 1. % de victoires Bleu vs Rouge
            victory_counts = {'Bleu': 0, 'Rouge': 0, 'Égalité': 0}
            for match in matches:
                if match.color_winner == 'blue':
                    victory_counts['Bleu'] += 1
                elif match.color_winner == 'red':
                    victory_counts['Rouge'] += 1
                else:
                    victory_counts['Égalité'] += 1

            charts['victories_blue_red'] = await loop.run_in_executor(None, self.generate_pie_chart, 
                '% victory RED / BLUE', victory_counts, 
                ['#1f77b4', '#ff7f0e', '#d62728']
            )

            # 2. Répartition des Objectifs Primaires
            primary_objectives = {obj: 0 for obj in VALID_OBJECTIVES_PRIMARY}
            for match in matches:
                primary_objectives[match.objective_primary] += 1

            charts['primary_objectives_distribution'] = await loop.run_in_executor(None, self.generate_pie_chart,
                'Primary objectives distribution',
                primary_objectives,
                sns.color_palette("Set2", len(primary_objectives)).as_hex()
            )

            # 3. Répartition des Objectifs Secondaires
            secondary_objectives = {obj: 0 for obj in VALID_OBJECTIVES_SECONDARY}
            for match in matches:
                secondary_objectives[match.objective_secondary] += 1

            charts['secondary_objectives_distribution'] = await loop.run_in_executor(None, self.generate_pie_chart,
                'Secondary objectives distribution',
                secondary_objectives,
                sns.color_palette("Set2", len(secondary_objectives)).as_hex()
            )

            # 4. Répartition des Avantages
            advantages = {adv: 0 for adv in VALID_ADVANTAGES}
            for match in matches:
                advantages[match.avantage_blue] += 1
                advantages[match.avantage_red] += 1

            charts['advantages_distribution'] = await loop.run_in_executor(None, self.generate_pie_chart,
                'Advantages distribution',
                advantages,
                sns.color_palette("Set2", len(advantages)).as_hex()
            )

            # 5. Répartition des Factions
            factions = {faction: 0 for faction in VALID_FACTIONS}
            for match in matches:
                # Récupérer les joueurs
                player_blue = session.query(Player).filter(Player.pseudo == match.player_blue).first()
                player_red = session.query(Player).filter(Player.pseudo == match.player_red).first()

                if player_blue and player_blue.faction in factions:
                    factions[player_blue.faction] += 1
                if player_red and player_red.faction in factions:
                    factions[player_red.faction] += 1

            charts['factions_distribution'] = await loop.run_in_executor(None, self.generate_pie_chart,
                'Factions distribution',
                factions,
                sns.color_palette("Set2", len(factions)).as_hex()
            )

            return charts

        except Exception as e:
            logger.error(f"Erreur lors de la génération des graphiques: {e}")
            return {}

    def generate_pie_chart(self, title, data, colors):
        """
        Génère un diagramme en secteurs et retourne un BytesIO contenant l'image.
        """
        fig, ax = plt.subplots(figsize=(6,6), facecolor='none')  # Fond transparent
        wedges, texts, autotexts = ax.pie(
            list(data.values()), 
            labels=list(data.keys()), 
            colors=colors, 
            autopct='%1.1f%%', 
            startangle=140,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )
        # Définir la couleur du titre à blanc
        ax.set_title(title, fontsize=14, fontweight='bold', color='white')

        # Définir la couleur des labels des secteurs à blanc
        for text in texts:
            text.set_color('white')
            text.set_weight('bold')
            text.set_fontsize(10)

        # Définir la couleur des autotexts (pourcentages) à blanc
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_fontsize(10)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        return buf

# Configuration du Cog
async def setup(bot: commands.Bot):
    """
    Fonction d'installation du Cog.
    """
    await bot.add_cog(StatsCog(bot))
