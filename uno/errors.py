# CARD ERRORS
class ColorNotSet(Exception):
    pass

# PLAYER ERRORS
class CardNotFound(Exception):
    pass


# GAME ERRORS
class BadCard(Exception):
    pass

class WrongPlayer(Exception):
    pass

class NotEnoughPlayers(Exception):
    pass

class GameNotStarted(Exception):
    pass

class GameInProgress(Exception):
    pass