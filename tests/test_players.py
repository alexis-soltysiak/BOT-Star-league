# test_data_manager.py

from data_manager import DataManager, Player

def test_add_and_load_players():
    # Ajouter un joueur
    new_player = Player(
        pseudo="TestPlayer",
        iddiscord="123456789012345678",
        displayname="Test Display",
        poule="A",
        faction="ArméeTest",
        liste="ListeTest"
    )
    DataManager.add_player(new_player)
    print(f"Joueur ajouté: {new_player.pseudo}")

    # Charger les joueurs
    players = DataManager.load_players()
    for player in players:
        print(f"Joueur: {player.pseudo}, Discord ID: {player.iddiscord}")


# test_data_manager.py


def test_load_players():
    players = DataManager.load_players()
    print(f"Nombre de joueurs: {len(players)}")
    for player in players:
        print(f"Pseudo: {player.pseudo}, ID Discord: {player.discord_id}")



if __name__ == "__main__":
    test_load_players()

