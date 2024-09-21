import os
import re
from datetime import datetime, timezone
from thefuzz import process  # Importer la fonction de correspondance

from dotenv import load_dotenv


class UtilitiesFunctions:
    MONTHS_FR = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }

    def format_joined_at(self, joined_at: datetime) -> str:
        day = joined_at.day
        month = self.MONTHS_FR[joined_at.month]
        year = joined_at.year
        hour = joined_at.hour
        minute = joined_at.minute

        return f"{day} {month} {year} à {hour}h{minute:02d}"

    @staticmethod
    def format_points(points: int, markdown: bool = False, win: bool = False) -> str:
        mkd = "**" if markdown else ""
        return ((f"{mkd}{points} point{mkd}" if points < 2 else f"{mkd}{points} points{mkd}") +
                ((" gagné" if points < 2 else " gagnés") if win else ""))

    @staticmethod
    def is_valid_date_format(date_str: str) -> bool:
        pattern = r"^\d{2}/\d{2} \d{2}h\d{2}$"

        if re.match(pattern, date_str):
            try:
                datetime.strptime(date_str, "%d/%m %Hh%M")
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def format_match_date(match_date: str, relative: bool = False) -> str:
        current_year = datetime.now().year
        match_date_with_year = f"{match_date} {current_year}"

        match_date = datetime.strptime(match_date_with_year, "%d/%m %Hh%M %Y")

        if match_date.tzinfo is None:
            match_date = match_date.replace(tzinfo=timezone.utc)

        timestamp = match_date.timestamp()

        formatted_date = match_date.strftime("%A %d %B à %Hh%M").capitalize()
        return f"{formatted_date} <t:{int(timestamp)}:R>" if relative else formatted_date

    @staticmethod
    def get_guild_id() -> int:
        load_dotenv(dotenv_path="config")
        return int(756600009985753107)




Utilities = UtilitiesFunctions()
