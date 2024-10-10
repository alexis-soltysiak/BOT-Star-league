import discord
import logging
from data_manager import DataManager, Match, Player 
from bdd.db_config import SessionLocal
from bdd.models import Admin,Classement
import functools
import math

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

def calculate_rankings_by_ligue_and_poule(ligue: str):
    session = SessionLocal()  # Create a session instance
    try:
        # Get all players in the league
        players = session.query(Player).filter(Player.ligue == ligue).all()

        # Organize players by poule
        players_by_poule = {}
        for player in players:
            poule = player.poule
            if poule not in players_by_poule:
                players_by_poule[poule] = {}
            players_by_poule[poule][player.pseudo] = {
                'points': 0,
                'vp': 0,
                'kp': 0,
                'matches_played': 0,
                'victories': 0,
                'opponents': set(),
                'sos': 0.0,
                'head_to_head': {},  # Stores head-to-head results
            }

        # Get all matches in the league
        matches = session.query(Match).filter(Match.ligue == ligue).all()

        # Process each match
        for match in matches:
            poule = match.poule
            stats_blue = players_by_poule.get(poule, {}).get(match.player_blue)
            stats_red = players_by_poule.get(poule, {}).get(match.player_red)

            # Update VP
            if stats_blue is not None:
                stats_blue['vp'] += match.vp_blue
            if stats_red is not None:
                stats_red['vp'] += match.vp_red

            # Update KP
            if stats_blue is not None:
                stats_blue['kp'] += match.kp_blue
            if stats_red is not None:
                stats_red['kp'] += match.kp_red

            # Update matches played
            if stats_blue is not None:
                stats_blue['matches_played'] += 1
            if stats_red is not None:
                stats_red['matches_played'] += 1

            # Update opponents
            if stats_blue is not None and stats_red is not None:
                stats_blue['opponents'].add(match.player_red)
                stats_red['opponents'].add(match.player_blue)

            # Update points, victories, and head-to-head
            if match.player_winner == match.player_blue:
                if stats_blue is not None:
                    stats_blue['points'] += 3
                    stats_blue['victories'] += 1
                    stats_blue['head_to_head'][match.player_red] = stats_blue['head_to_head'].get(match.player_red, 0) + 1
                if stats_red is not None:
                    stats_red['points'] += 0
            elif match.player_winner == match.player_red:
                if stats_red is not None:
                    stats_red['points'] += 3
                    stats_red['victories'] += 1
                    stats_red['head_to_head'][match.player_blue] = stats_red['head_to_head'].get(match.player_blue, 0) + 1
                if stats_blue is not None:
                    stats_blue['points'] += 0
            else:
                # Draw
                if stats_blue is not None:
                    stats_blue['points'] += 1
                    stats_blue['head_to_head'][match.player_red] = stats_blue['head_to_head'].get(match.player_red, 0) + 0.5
                if stats_red is not None:
                    stats_red['points'] += 1
                    stats_red['head_to_head'][match.player_blue] = stats_red['head_to_head'].get(match.player_blue, 0) + 0.5

        # Calculate SoS for each player
        for poule, players_stats in players_by_poule.items():
            for player_pseudo, stats in players_stats.items():
                sos_sum = 0.0
                for opponent_pseudo in stats['opponents']:
                    opponent_stats = players_stats.get(opponent_pseudo)
                    if opponent_stats and opponent_stats['matches_played'] > 0:
                        opponent_victories = opponent_stats['victories']
                        opponent_matches_played = opponent_stats['matches_played']
                        sos_sum += opponent_victories / opponent_matches_played
                if stats['matches_played'] > 0 and len(stats['opponents']) > 0:
                    stats['sos'] = sos_sum / len(stats['opponents'])
                else:
                    stats['sos'] = 0.0

        # Define the comparison function
        def compare_players(item1, item2):
            pseudo1, stats1 = item1
            pseudo2, stats2 = item2

            # Primary sort: Points
            if stats1['points'] != stats2['points']:
                return stats2['points'] - stats1['points']

            # Tie-breaker 1: Head-to-head confrontation
            h2h1 = stats1['head_to_head'].get(pseudo2, 0)
            h2h2 = stats2['head_to_head'].get(pseudo1, 0)
            if h2h1 != h2h2:
                return int(h2h1 - h2h2)  # Correction ici

            # Tie-breaker 2: SoS
            if not math.isclose(stats1['sos'], stats2['sos'], rel_tol=1e-9):
                return -1 if stats2['sos'] > stats1['sos'] else 1

            # Tie-breaker 3: VP 
            if stats1['vp'] != stats2['vp']:
                return stats2['vp'] - stats1['vp']
            
            # Tie-breaker 4: KP 
            if stats1['kp'] != stats2['kp']:
                return stats2['kp'] - stats1['kp']

            # If still tied, maintain original order
            return 0

        # Create the ranking list for each poule
        rankings_by_poule = {}
        for poule, players_stats in players_by_poule.items():
            ranking_list = list(players_stats.items())
            ranking_list.sort(key=functools.cmp_to_key(compare_players))
            rankings_by_poule[poule] = ranking_list

        # Clear existing classement data for this league
        session.query(Classement).filter(Classement.ligue == ligue).delete()
        session.commit()

        # Save the results into the 'classement' table
        for poule, ranking_list in rankings_by_poule.items():
            for rank, (player_pseudo, stats) in enumerate(ranking_list, start=1):
                classement = Classement(
                    ligue=ligue,
                    poule=poule,
                    player_pseudo=player_pseudo,
                    points=stats['points'],
                    vp=stats['vp'],
                    kp=stats['kp'],
                    matches_played=stats['matches_played'],
                    victories=stats['victories'],
                    sos=stats['sos'],
                )
                #session.add(classement)
        #session.commit()

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
    Utilise trois colonnes dans les blocs de code pour séparer les joueurs bleus et rouges avec l'emoji de résultat.
    Ajoute une légende en haut avec une ligne de séparation et un emoji d'épée croisée.
    Ajoute un emoji de coupe 🏆 à côté du vainqueur.
    Limite la taille des pseudos à 15 caractères.
    """
    # Définir les largeurs des colonnes
    WIDTH_PLAYER = 13  # Augmenté pour tenir compte des emojis
    WIDTH_RESULT = 6  # Augmenté pour les emojis de résultat

    def format_player(name: str, is_winner: bool) -> str:
        """
        Formate le nom du joueur en le tronquant si nécessaire et en ajoutant l'emoji 🏆 si c'est le vainqueur.
        Ajoute des espaces supplémentaires pour maintenir l'alignement.
        """
        if is_winner:
            # Réserver de l'espace pour l'emoji 🏆
            max_length = WIDTH_PLAYER - 4  # 2 pour l'espace et 2 pour l'emoji
            if len(name) > max_length - 3:
                name = name[:max_length - 3] + '...'
            return f"{name}".ljust(WIDTH_PLAYER)
        else:
            if len(name) > WIDTH_PLAYER - 3:
                return name[:WIDTH_PLAYER - 6] + '...  '.ljust(WIDTH_PLAYER)
            return name.ljust(WIDTH_PLAYER)

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
            
            # Initialiser le contenu avec un bloc de code triple
            description = "```\n"
            
            # Ajouter la légende et la ligne de séparation
            header_blue = "Joueur Bleu".ljust(WIDTH_PLAYER)
            header_result = "VS".center(WIDTH_RESULT)
            header_red = "Joueur Rouge".ljust(WIDTH_PLAYER)
            description += f"{header_blue} {header_result} {header_red}\n"
            description += f"{'-' * WIDTH_PLAYER} {'-' * WIDTH_RESULT} {'-' * WIDTH_PLAYER}\n"
            
            for match in matches:
                # Déterminer le vainqueur
                if match.player_winner == match.player_blue:
                    resultat = "🏆⚔️🧸"
                    player_blue_display = format_player(match.player_blue, True)
                    player_red_display = format_player(match.player_red, False)
                elif match.player_winner == match.player_red:
                    resultat = "🧸⚔️🏆"
                    player_blue_display = format_player(match.player_blue, False)
                    player_red_display = format_player(match.player_red, True)
                else:
                    # En cas d'égalité ou autre cas
                    resultat = "🧸⚔️🧸"
                    player_blue_display = format_player(match.player_blue, False)
                    player_red_display = format_player(match.player_red, False)
                
                # Assurer que chaque champ a la bonne longueur
                resultat = resultat.center(WIDTH_RESULT)
                
                # Ajouter les informations aux colonnes
                description += f"{player_blue_display} {resultat} {player_red_display}\n"
            
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
        # Trier les poules par ordre alphabétique
        poules_tries = sorted(rankings_by_poule.keys())
        
        for poule in poules_tries:
            ranking_list = rankings_by_poule[poule]
            
            # Titre de la poule avec emoji si nécessaire
            poule_title = f"Poule {poule.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}"
            
            # En-tête des colonnes
            description = "```\n"
            description += f"{'Rank':<6} {'Pseudo':<15} {'Points':<6}\n"
            description += f"{'-'*6} {'-'*15} {'-'*6}\n"
            
            # Ajout des joueurs dans le classement
            for rank, (pseudo, stats) in enumerate(ranking_list, start=1):
                # Limiter le pseudo à 15 caractères avec des ellipses si nécessaire
                pseudo_display = (pseudo[:12] + '...') if len(pseudo) > 15 else pseudo.ljust(15)
                description += f"{rank:<6} {pseudo_display:<15} {stats['points']:<6}\n"
            
            description += "```"
            
            # Ajouter le champ avec le classement de la poule
            embed.add_field(name=poule_title, value=description, inline=False)
    
    return embed



def create_advanced_combined_rankings_embed(rankings_by_poule: dict, ligue: str) -> discord.Embed:

    embed = discord.Embed(
        title=f"Classement Avancé pour la ligue {ligue.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}",
        color=discord.Color.dark_gold()
    )
    
    if not rankings_by_poule:
        embed.description = "Aucun joueur trouvé pour cette ligue."
    else:
        # Trier les poules par ordre alphabétique
        poules_tries = sorted(rankings_by_poule.keys())
        
        for poule in poules_tries:
            ranking_list = rankings_by_poule[poule]
            
            # Titre de la poule avec emoji si nécessaire
            poule_title = f"Poule {poule.capitalize()} {DICT_EMOJI_LIGUES_DISPLAY.get(ligue.lower(), '')}"
            
            # En-tête des colonnes
            description = "```\n"
            description += f"{'Rk':<3} {'Psd':<8} {'Pts':<4} {'SoS':<5} {'VP':<4} {'KP':<4}\n"
            description += f"{'-'*3} {'-'*8} {'-'*4} {'-'*5} {'-'*4} {'-'*4}\n"
            
            # Ajout des joueurs dans le classement
            for rank, (pseudo, stats) in enumerate(ranking_list, start=1):
                # Limiter le pseudo à 5 caractères avec des ellipses si nécessaire
                pseudo_display = (pseudo[:8]) if len(pseudo) > 5 else pseudo.ljust(8)
                sos_display = f"{stats['sos']:.2f}"
                description += f"{rank:<3} {pseudo_display:<8} {stats['points']:<4} {sos_display:<5} {stats['vp']:<4} {stats['kp']:<4}\n"
            
            description += "```"
            
            # Ajouter le champ avec le classement avancé de la poule
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