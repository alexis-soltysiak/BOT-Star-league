import discord
import logging
from data_manager import DataManager, Match, Player
from bdd.db_config import SessionLocal
from bdd.models import Admin

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from variables import VALID_LIGUES, VALID_FACTIONS, SCORE_PROXIMITY, VALID_STATUSES, VALID_OBJECTIVES_PRIMARY, VALID_OBJECTIVES_SECONDARY, VALID_ADVANTAGES, DICT_EMOJI_LIGUES_DISPLAY



def admin_required(interaction: discord.Interaction) -> bool:
    cog = interaction.client.get_cog('AdminMatchs')
    if cog is None:
        logger.warning("Cog 'AdminMatchs' non trouvé.")
        return False
    is_admin = cog.is_user_admin(interaction.user.id)
    logger.info(f"Vérification admin pour {interaction.user.id}: {is_admin}")
    return is_admin



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
    Utilise les colonnes de l'embed pour séparer les joueurs bleus et rouges avec leurs VP.
    Ajoute une légende en haut avec une ligne de séparation et un emoji d'épée croisée.
    Ajoute un emoji de coupe 🏆 à côté du vainqueur.
    Limite la taille des pseudos à 15 caractères.
    """
    embed = discord.Embed(
        title=f"Matchs pour la ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}",
        color=discord.Color.blue()
    )
    
    if not matches_by_poule:
        embed.description = "Aucun match trouvé pour cette ligue."
    else:
        for poule, matches in matches_by_poule.items():
            # Titre de la poule avec emoji si nécessaire
            poule_title = f"Poule {poule.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}"
            
            # Initialiser le contenu du bloc de code
            description = "```\n"
            
            # Ajouter la légende et la ligne de séparation
            description += f"{'Joueur Bleu':<15} 🗡️ {'Joueur Rouge':<15}\n"
            description += f"{'-'*15} 🗡️ {'-'*15}\n"
            
            for match in matches:
                # Limiter le pseudo à 15 caractères avec des ellipses si nécessaire
                player_blue = (match.player_blue[:12] + '...') if len(match.player_blue) > 15 else match.player_blue
                player_red = (match.player_red[:12] + '...') if len(match.player_red) > 15 else match.player_red
                
                # Déterminer le vainqueur et ajouter l'emoji de coupe 🏆
                if match.player_winner == match.player_blue:
                    blue_vp = f"🥇 {match.vp_blue} 🏆"
                    red_vp = f"🥇 {match.vp_red}"
                elif match.player_winner == match.player_red:
                    blue_vp = f"🥇 {match.vp_blue}"
                    red_vp = f"🥇 {match.vp_red} 🏆"
                else:
                    blue_vp = f"🥇 {match.vp_blue}"
                    red_vp = f"🥇 {match.vp_red}"
                
                # Ajouter les informations aux colonnes avec l'emoji d'épée croisée
                description += f"🗡️ {player_blue:<14} 🗡️ {player_red:<14}\n"
                description += f"{blue_vp:<15} 🗡️ {red_vp:<15}\n\n"
            
            description += "```"
            
            # Ajouter le champ pour le nom de la poule suivi des résultats
            embed.add_field(
                name=poule_title,
                value=description,
                inline=False
            )
    
    return embed








def add_banner_to_embed(embed: discord.Embed, filename: str = "baniere.png") -> discord.Embed:
    embed.set_image(url=f"attachment://{filename}")
    return embed


def create_combined_rankings_embed(rankings_by_poule: dict, ligue: str) -> discord.Embed:

    embed = discord.Embed(
        title=f"Classement pour la ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}",
        color=discord.Color.gold()
    )
    
    if not rankings_by_poule:
        embed.description = "Aucun joueur trouvé pour cette ligue."
    else:
        for poule, ranking_list in rankings_by_poule.items():
            # Titre de la poule avec emoji si nécessaire
            poule_title = f"Poule {poule.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}"
            
            # En-tête des colonnes
            description = "```\n"
            description += f"{'Rank':<6} {'Pseudo':<15} {'Points':<6}\n"
            description += f"{'-'*6} {'-'*15} {'-'*6}\n"
            
            # Ajout des joueurs dans le classement
            for rank, (pseudo, stats) in enumerate(ranking_list, start=1):
                # Limiter le pseudo à 15 caractères avec des ellipses si nécessaire
                pseudo_display = (pseudo[:12] + '...') if len(pseudo) > 15 else pseudo
                description += f"{rank:<6} {pseudo_display:<15} {stats['points']:<6}\n"
            
            description += "```"
            
            # Ajouter le champ avec le classement de la poule
            embed.add_field(name=poule_title, value=description, inline=False)
    
    return embed


def admin_required(interaction: discord.Interaction) -> bool:
    is_admin = is_user_admin(interaction.user.id)
    logger.info(f"Vérification admin pour {interaction.user.id}: {is_admin}")
    return is_admin

def is_user_admin(discord_id: int) -> bool:
        with SessionLocal() as session:
            admin = session.query(Admin).filter_by(discord_id=str(discord_id), is_admin=True).first()
            if admin:
                logger.info(f"Admin trouvé pour l'ID Discord: {discord_id}")
                return True
            else:
                logger.info(f"Aucun admin trouvé pour l'ID Discord: {discord_id}")
                return False