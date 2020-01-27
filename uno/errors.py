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

# NOT ERRORS
class DrawAndSkipPlayer(Exception):
    def __init__(self, player, draw_amount):
        self.player = player
        self.draw_amount = draw_amount

class SkipPlayer(Exception):
    def __init__(self, player):
        self.player = player

class Reversed(Exception):
    pass