import difflib
import json
from datetime import datetime
import csv
from enum import Enum

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from bdd.db_config import SessionLocal
from bdd.models import Base,Player, Match
import os
from dotenv import load_dotenv
from typing import Optional, Tuple



class DataManagerFunctions:
    def __init__(self):
        self.db: Session = SessionLocal

    def close_connection(self):
        self.db.close()

    # PLAYERS
    def add_player(self, player: Player):
        with self.db() as session:
            session.add(player)
            session.commit()
            session.refresh(player)

    def load_players(self) -> list[Player]:
        with self.db() as session:
            return session.query(Player).all()

    def get_player_info(self, pseudo: str) -> Player | None:
        with self.db() as session:
            return session.query(Player).filter(Player.pseudo == pseudo).first()

    def get_all_player_pseudos(self) -> list[str]:
        with self.db() as session:
            return [pseudo for (pseudo,) in session.query(Player.pseudo).all()]
        
    def get_display_name_by_pseudo(self, pseudo: str) -> str:
        with self.db() as session:
            player = session.query(Player).filter(Player.pseudo == pseudo).first()
            return player.display_name if player else None
        
    def get_league_and_group_by_pseudo(self, pseudo: str) -> Optional[Tuple[str, str]]:
        with self.db() as session:
            player = session.query(Player).filter(Player.pseudo == pseudo).first()
            if player:
                return (player.ligue, player.poule)
            return None

    def get_player_info_by_iddiscord(self, iddiscord: str) -> Player | None:
        with self.db() as session:
            return session.query(Player).filter(Player.iddiscord == iddiscord).first()


    # MATCHS
    def add_match(self, match: Match):
        with self.db() as session:
            session.add(match)
            session.commit()
            session.refresh(match)

    def load_matches(self) -> list[Match]:
        with self.db() as session:
            return session.query(Match).all()
        
    def load_latest_matches(self, limit: int = 3) -> list[Match]:
        with self.db() as session:
            return session.query(Match).order_by(Match.created_at.desc()).limit(limit).all()
        
    def load_matches_from_ligue(self,ligue: str) -> list[Match]:
        with self.db() as session:
            return session.query(Match).filter(Match.ligue == ligue).all()

    def get_match_from_id(self, match_id: int) -> Match | None:
        with self.db() as session:
            return session.query(Match).filter(Match.id == match_id).first()

    def get_new_match_id(self) -> int:
        with self.db() as session:
            last_match = session.query(Match).order_by(Match.id.desc()).first()
            return last_match.id + 1 if last_match else 1
        
    def match_exists(self, player_blue: str, player_red: str, status: str) -> bool:
        """
        Vérifie si un match avec les mêmes player_blue, player_red et status existe déjà.
        """
        with self.db() as session:
            match = session.query(Match).filter(
                Match.player_blue == player_blue,
                Match.player_red == player_red,
                Match.status == status
            ).first()
            return match is not None

DataManager = DataManagerFunctions()