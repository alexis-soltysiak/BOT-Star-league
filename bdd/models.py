# models.py

from sqlalchemy import Column, Integer, String, ForeignKey,Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True, index=True)
    pseudo_discord = Column(String, unique=True, index=True, nullable=False)
    discord_id = Column(String, unique=True, index=True, nullable=False)
    is_admin = Column(Boolean, default=True)

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, index=True)
    pseudo = Column(String, unique=True, index=True, nullable=False)
    discord_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    ligue = Column(String, nullable=False)
    poule = Column(String, nullable=False)
    armee = Column(String, nullable=False)
    liste = Column(String, nullable=False)
    is_admin = Column(String, nullable=False)


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)
    ligue = Column(String, nullable=False)
    poule = Column(String, nullable=False)
    player_blue = Column(String, ForeignKey('players.pseudo'), nullable=False)
    player_red = Column(String, ForeignKey('players.pseudo'), nullable=False)
    player_winner = Column(String, ForeignKey('players.pseudo'), nullable=True)
    color_winner = Column(String, nullable=True)
    vp_blue = Column(Integer, nullable=False)
    vp_red = Column(Integer, nullable=False)
    objective_primary = Column(String, nullable=False)
    objective_secondary = Column(String, nullable=False)
    avantage_blue = Column(String, nullable=False)
    avantage_red = Column(String, nullable=False)
    kp_blue = Column(Integer, nullable=False)
    kp_red = Column(Integer, nullable=False)
