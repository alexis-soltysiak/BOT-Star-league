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

"""

# Charger les variables d'environnement
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

"""


class DataManagerFunctions:
    def __init__(self):
        self.db: Session = SessionLocal

    def close_connection(self):
        self.db.close()

    # Méthodes pour gérer les joueurs
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
    
    def get_player_info_by_iddiscord(self, iddiscord: str) -> Player | None:
        with self.db() as session:
            return session.query(Player).filter(Player.iddiscord == iddiscord).first()

    # Méthodes pour gérer les matchs
    def add_match(self, match: Match):
        with self.db() as session:
            session.add(match)
            session.commit()
            session.refresh(match)

    def load_matches(self) -> list[Match]:
        with self.db() as session:
            return session.query(Match).all()

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


DataManager = DataManagerFunctions()