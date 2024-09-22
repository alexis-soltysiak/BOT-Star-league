import locale
import platform
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))


os_name = platform.system()
if os_name == "Windows":
    locale.setlocale(locale.LC_TIME, "fra")
elif os_name == "Linux":
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


bot: commands.bot.Bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
guild: discord.Guild


cogs = ["cogs.help","cogs.player_match"]


async def setup_cogs():
    for ext in cogs:
        try:
            await bot.load_extension(ext)
            print(f"Cog {ext} chargé avec succès.")
        except Exception as e:
            print(f"Erreur lors du chargement du cog {ext}: {e}")




@bot.event
async def on_ready():

    await setup_cogs()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # Synchroniser les commandes pour la guilde spécifique

    try:
        synced = await bot.tree.sync()
        print("Le bot est désormais synchronisé avec " + str(len(synced)) + " commandes:")
        for cmd in synced:
            print("- " + cmd.name)
    except Exception as e:
        print("Le bot n'est pas synchronisé: " + str(e))


def get_cogs_status(cogs_status) -> tuple[bool, bool]:
    has_errors = False
    has_started = False
    for cog, status in cogs_status.items():
        if status == "loaded":
            has_started = True
        elif status.startswith("error: "):
            has_errors = True
    return has_errors, has_started



async def display_cogs_status_embed(message, cogs_status, finished=False):
    has_errors, has_started = get_cogs_status(cogs_status)
    color = 0xff0000 if has_errors else 0x00ff00 if finished else 0xffd700 if has_started else 0x2b2d31

    if finished:
        embed = discord.Embed(title="Rechargement des cogs terminé !", color=color)
    else:
        embed = discord.Embed(title="Rechargement des cogs...", color=color)

    for cog, status in cogs_status.items():
        if status == "loading":
            embed.add_field(name=f"🔁 `{cog}`", value="```ansi\n[0;36;48mChargement...```", inline=False)
        elif status == "loaded":
            embed.add_field(name=f"✅ `{cog}`", value="```ansi\n[0;32;48mChargé avec succès```", inline=False)
        elif status.startswith("error: "):
            error_message = status[len("error: "):]
            embed.add_field(name=f"❌ `{cog}`", value=f"```ansi\n[0;31;48mErreur: {error_message}```", inline=False)

    await message.edit(embed=embed)



@bot.tree.command(name="reload", description="Recharge les cogs du bot")
async def cmd_reload(interaction: discord.Interaction):
    await interaction.response.defer()

    message = await interaction.followup.send(
        content="**Rechargement des cogs...**",
        embed=discord.Embed(title="Initialisation...", color=0x2b2d31)
    )

    cogs_status = {cog: "loading" for cog in cogs}
    await display_cogs_status_embed(message, cogs_status)

    for cog in cogs:
        try:
            await bot.reload_extension(cog)
            cogs_status[cog] = "loaded"
        except Exception as e:
            error_str = str(e)
            print(f"Erreur lors du rechargement de {cog}: {error_str}")
            cogs_status[cog] = f"error: {error_str}"

        await display_cogs_status_embed(message, cogs_status)

    await display_cogs_status_embed(message, cogs_status, True)


bot.run(DISCORD_TOKEN)