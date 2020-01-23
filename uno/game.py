from .deck import Deck, PlayerDeck
from .card import ColorCard, SpecialCard, WildCard

from .errors import NotEnoughPlayers, GameNotStarted, GameInProgress, BadCard, WrongPlayer

class UnoGame:
    """[summary]
    
    Raises:
        NotEnoughPlayers: [description]
        GameNotStarted: [description]
        WrongPlayer: [description]
        BadCard: [description]
        TypeError: [description]
        GameInProgress: [description]
    """    
    def __init__(self, players = [], deck_size = 2):
        """[summary]
        
        Keyword Arguments:
            players {list} -- [description] (default: {[]})
            deck_size {int} -- [description] (default: {2})
        """        
        self.started = False
        self.players = players
        self.deck = Deck(deck_size)

    # TODO: make first card not a special
    # TODO: handle multiple skips/plus_2s???
    def start_game(self):
        """[summary]
        
        Raises:
            NotEnoughPlayers: [description]
        """        
        if len(self.players) < 2:
            raise NotEnoughPlayers

        for player in self.players:
            player.deck = PlayerDeck(self.deck.distribute(7))

        self._players_iter = iter(self.players)
        self._current_player = next(self._players_iter)

        self.history = [self.deck.pop()]

        self.started = True

    @property
    def last_card(self):
        """
        Returns:
            Card -- last played card
        """        
        return self.history[-1]

    def play(self, player, card):
        """[summary]
        
        Arguments:
            player {Object} -- any object with a object.deck
            card {Card} -- card to be played
        
        Raises:
            GameNotStarted: [description]
            WrongPlayer: [description]
            BadCard: [description]
            TypeError: [description]
        """        
        if not self.started: raise GameNotStarted
        if not player == self._current_player: raise WrongPlayer
        if not player.deck.has(card): raise BadCard
        
        last_card = self.last_card
        if isinstance(card, (ColorCard, SpecialCard)):
            last_card.compare(card)
        elif isinstance(card, WildCard):
            pass
        else: raise TypeError("expected type ColorCard || SpecialCard || WildCard not %s." % type(card))

        player.deck.remove(card)
        self.history.append(card)

        if isinstance(card, (SpecialCard, WildCard)):
            if card.special.startswith("PLUS_"):
                draw_amount = int(card.special.split("_", 1)[1])
                cards = self.deck.distribute(draw_amount)

                player = self._next_player()
                player.deck.extend(cards)
            elif card.special == "REVERSE":
                self.players.reverse()
            elif card.special == "SKIP":
                self._next_player()

        self._next_player()

    def add_player(self, player):
        """
        Arguments:
            player {Object} -- any object, object.deck will be used to store PlayerDeck
        
        Raises:
            GameInProgress: [description]
        """        
        if self.started: raise GameInProgress
        self.players.append(player)

    def _next_player(self):
        try:
            self._current_player = next(self._players_iter)
        except StopIteration:
            self._players_iter = iter(self.players)
            self._current_player = next(self._players_iter)
        finally:
            return self._current_player