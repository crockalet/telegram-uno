import weakref

from functools import cached_property

import telegram

from uno import UnoGame

class GameNotFound(Exception): pass
class PlayerAlreadyInGame(Exception): pass
class PlayerNotFound(Exception): pass
class NoContext(Exception): pass

class Context:
    def __init__(self):
        self.foo = 'bar'

class UnoTelegramGame(UnoGame):
    # TODO: cached properties?
    def __init__(self, context, chat):
        super().__init__(players=[], deck_size=2)
        self.chat = chat
        context.chat_data['uno'] = self

    def add_user(self, context, user):
        if self.has_player(user): raise PlayerAlreadyInGame
        
        super().add_player(UnoTelegramPlayer(user, self, context))

    def remove_user(self, user):
        if self.has_player(user): self.players.remove(user)
        else: raise PlayerNotFound

    def has_player(self, player):
        if player in self.players: return True
        else: return False

    def cleanup(self, context):
        del context.chat_data['uno']

    @property
    def current_player(self):
        return self._current_player

    @property
    def current_player_text(self):
        f"{self.current_player}`, your turn`"

    @property
    def players_text(self):
        return ', '.join(str(player) for player in self.players)

    @property
    def start_text(self):
        return f"Welcome to Uno.\nClick below to join or start game.\n\n`joined:`\n{self.players_text}"

    @cached_property
    def chat_id(self):
        return str(self.chat.id)

    @staticmethod
    def get_game(context, chat):
        try:
            game = context.chat_data['uno']
            if not isinstance(game, UnoTelegramGame): raise GameNotFound(f"Chat data object: {game}")

            return game
        except KeyError:
            raise GameNotFound
        
    @staticmethod
    def in_chat(context, chat):
        """Check if game in progress in chat
        
        Arguments:
            context {telegram.ext.CallbackContext} -- []
            chat {telegram.Chat} -- []
        
        Returns:
            [bool] -- 
        """        
        try:
            context.chat_data['uno']
            return True
        except KeyError:
            return False

class UnoTelegramPlayer:
    def __init__(self, user, game, context):
        # TODO: weakref user?
        self.user = user
        self._game = weakref.ref(game)
        context.user_data['uno'] = weakref.ref(self)

    def __str__(self):
        return self.user.mention_markdown()

    def __eq__(self, other):
        return other == self.user if isinstance(other, telegram.User) else self.user == other.user

    def cleanup(self, context):
        del context.user_data['uno']

    @property
    def game(self):
        game = self._game()
        if game is not None: return game
        else: raise GameNotFound

    @cached_property
    def user_id(self):
        return str(self.user.id)
    
    @staticmethod
    def get_player(context, user):
        try:
            player = context.user_data['uno']
            if not isinstance(player, weakref.ref): raise PlayerNotFound(f"User data object: {player}")

            player = player()
            if player is None: raise PlayerNotFound(f"User ID: {user.id}")
            elif not isinstance(player, UnoTelegramPlayer): raise PlayerNotFound(f"User data object: {player}")

            return player
        except KeyError:
            raise PlayerNotFound
        

    

    