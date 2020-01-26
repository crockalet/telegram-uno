from collections import Counter
from copy import deepcopy
from random import shuffle

from .card import CARDS
from .errors import CardNotFound

def generate_deck(amount):
    deck = []
    for i in range(amount):
        deck.extend(deepcopy(CARDS))

    shuffle(deck)

    return deck

class Deck:
    def __init__(self, amount = 2):
        self._deck = generate_deck(amount)

    def pop(self):
        try:
            return self._deck.pop()
        except IndexError:
            self._deck.extend(generate_deck(1))
            return self._deck.pop()

    def distribute(self, amount = 7):
        cards = []
        while len(cards) < amount:
            try:
                cards.append(self._deck.pop())
            except IndexError:
                self._deck.extend(generate_deck(1))
        
        return cards

        # cards = self._deck[:amount]
        # del self._deck[:amount]
        # card_l = len(cards)

        # if (card_l < amount):
        #     self._cards.extend(generate_deck(1))
        #     cards.extend(self._deck[:amount - card_l])
        #     del self._deck[:amount - card_l]

        # return cards

class PlayerDeck:
    def __init__(self, deck = []):
        self._deck = deck
        
    def push(self, card):
        self._deck.append(card)

    def extend(self, cards):
        self._deck.extend(cards)

    @property
    def view(self):
        """
        Returns:
            collections.Counter -- key: card, value: count
        """
        return Counter(self._deck)

    @property
    def len(self):
        return len(self._deck)

    def remove(self, card):
        try:
            self._deck.remove(card)
        except ValueError:
            raise CardNotFound(f"{card} not in {self._deck}")



    
