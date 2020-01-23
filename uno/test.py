from . import game as uno

from .errors import BadCard, WrongPlayer
from .card import WildCard, COLORS

import time
import logging

from random import choice

logging.basicConfig(level=logging.INFO)

class TestPlayer:
    def __init__(self, i): self.i = i
    def __str__(self): return "Player %s" % self.i


def randomized_test(player_amount = 4, delay = 0.5):
    """ 
    Keyword Arguments:
        player_amount {int} -- [] (default: {4})
        delay {float} -- [delay in seconds] (default: {0.5})
    """    
    players = []
    for i in range(player_amount):
        players.append(TestPlayer(i))

    game = uno.UnoGame(players)
    game.start_game()

    logging.info(game.last_card)

    leastcards = 1

    while leastcards > 0:
        for player in players:
            if leastcards == 0:
                break
            
            played = False
            cards = iter(player.deck._deck)

            while not played:
                last_card = game.last_card
                try:
                    card = next(cards)
                except StopIteration:
                    card = game.deck.pop()
                    player.deck.push(card)
                    logging.debug("LAST: %s, DECK %s" % (game.last_card, player.deck.view))
                    logging.info("%s drew card %s" % (player, card))

                if isinstance(card, WildCard):
                    card.set_color(choice(COLORS))

                try:
                    logging.debug("LAST: %s, NOW: %s" % (last_card, card))
                    game.play(player, card)
                    
                    logging.info("%s played %s against %s." % (player, card, last_card))
                    played = True
                except BadCard:
                    continue
                except WrongPlayer:
                    logging.debug("%s is not the current player" % player)
                    break

                if player.deck.len < leastcards:
                    logging.debug("%s has %i cards" % (player, player.deck.len))
                    leastcards = player.deck.len
                if player.deck.len == 1:
                    logging.info("%s: UNO! %s" % (player, player.deck.view))
                if player.deck.len == 0:
                    logging.info("%s won!!" % player)

            time.sleep(delay)





