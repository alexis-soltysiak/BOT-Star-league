# models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func,Boolean,UniqueConstraint, Float

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
    faction = Column(String, nullable=False)
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Adding the Classement table
class Classement(Base):
    __tablename__ = 'classement'
    id = Column(Integer, primary_key=True, index=True)
    ligue = Column(String, nullable=False, index=True)
    poule = Column(String, nullable=False, index=True)
    player_pseudo = Column(String, ForeignKey('players.pseudo'), nullable=False, index=True)
    points = Column(Integer, default=0, nullable=False)
    vp = Column(Integer, default=0, nullable=False)
    kp = Column(Integer, default=0, nullable=False)
    matches_played = Column(Integer, default=0, nullable=False)
    victories = Column(Integer, default=0, nullable=False)
    sos = Column(Float, default=0.0, nullable=False)

    __table_args__ = (
        UniqueConstraint('ligue', 'poule', 'player_pseudo', name='_ligue_poule_player_uc'),
    )