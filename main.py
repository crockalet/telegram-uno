import logging
import configparser

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, PhotoSize,
                    InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import (Updater, CommandHandler, MessageHandler, CallbackQueryHandler, 
                        InlineQueryHandler)

import uno
from uno_telegram import (UnoTelegramGame,UnoTelegramPlayer, GameNotFound, PlayerNotFound,
                            PlayerAlreadyInGame)

config = configparser.ConfigParser()
config.read('config.ini')

API_TOKEN = config['bot']['API_TOKEN']

# TODO: image link dict
PLACEHOLDER_IMG = "https://i.imgur.com/LuR9Rw1.jpg"

logging.basicConfig(level=logging.INFO)

join_button = InlineKeyboardButton("Join", callback_data="join")
start_button = InlineKeyboardButton("Start", callback_data="start")

play_button = InlineKeyboardButton("play", switch_inline_query_current_chat="play")
view_button = InlineKeyboardButton("👁", switch_inline_query_current_chat="cards")
view_all_button = InlineKeyboardButton("📊", callback_data="view_all")

leave_button = InlineKeyboardButton("❌", callback_data="leave")

join_keyboard = [
    [join_button, leave_button],
        [start_button]
    ]
join_markup = InlineKeyboardMarkup(join_keyboard)

play_keyboard = [
                [play_button],
    [view_button, view_all_button, leave_button]
]
play_markup = InlineKeyboardMarkup(play_keyboard)



CARD_IMAGE_CACHE = dict()
# TODO: threadsafe singleton cache?
# TODO: cache all files at start?
def cached_image(id_, location, func, **kwargs):
    """runs func with cached image as a param
    
    Arguments:
        id {str} -- id to get or save
        location {str} -- image dir to open
        func {function} -- function to call with image
    """    
    try:
        image = CARD_IMAGE_CACHE[id_]
        return func(photo=image, **kwargs)
    except KeyError:
        image = func(photo=open(location, 'rb'), **kwargs)
        CARD_IMAGE_CACHE[id_] = image.photo[0]

def start(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if UnoTelegramGame.in_chat(context, chat):
        return user.send_message(text=f"Game already in progress in {chat.title}.")

    if not (chat.type == chat.GROUP or chat.type == chat.SUPERGROUP):
        return chat.send_message(
            text=f"Can only start uno game in {chat.GROUP} or {chat.SUPERGROUP} not in {chat.type}.")

    game = UnoTelegramGame(context, chat)

    return chat.send_message(text=game.start_text, 
        reply_markup=join_markup, 
        parse_mode=ParseMode.MARKDOWN)

def join(update, context):
    query = update.callback_query
    user = query.from_user
    message = query.message
    chat = message.chat

    if not UnoTelegramGame.in_chat(context, chat):
        return query.answer(text="❌ No game found.", show_alert=True)
    
    game = UnoTelegramGame.get_game(context, chat)

    try:
        game.add_user(context, user)
    except PlayerAlreadyInGame:
        return query.answer(text="❌ You're already in this game!")
    
    query.answer()
    return message.edit_text(game.start_text, reply_markup=join_markup, parse_mode=ParseMode.MARKDOWN)


def start_game(update, context):
    query = update.callback_query
    user = query.from_user
    message = query.message
    chat = message.chat

    if not UnoTelegramGame.in_chat(context, chat):
        return query.answer(text="❌ No game found.", show_alert=True)

    game = UnoTelegramGame.get_game(context, chat)

    ## TODO: check if admin/owner

    ## TODO: randomize players
    try:
        game.start_game()
    except uno.errors.NotEnoughPlayers:
        return query.answer(text="❌ Not enough players!", show_alert=True)
    text = game.start_text + "\n\n`[-- GAME STARTED --]`"
    
    message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    caption = "%s" % game.last_card
    cached_image('uno', 'placeholder.png', chat.send_photo,
                caption=f"{game.last_card}, {game.current_player_text}", reply_markup=play_markup)

def play(update, context):
    query = update.inline_query
    user = query.from_user

    try:
        player = UnoTelegramPlayer.get_player(context, user)
        
        game = player.game
        chat = game.chat

        if not game.started: raise PlayerNotFound
    except PlayerNotFound:
        return query.answer(results=[], switch_pm_text="❌ You don't seem to be in a game!",
                            switch_pm_parameter="not_in_game", cache_time=0)

    NOT_CURRENT_PLAYER = not user == game.current_player
    default_message = InputTextMessageContent('A?')

    results = []
    for card, amount in player.deck.view.items():
        if NOT_CURRENT_PLAYER:
            results.append(
                InlineQueryResultPhoto(f"no_play_{card}", PLACEHOLDER_IMG, PLACEHOLDER_IMG, title=str(card),
                                        description=f"You have {amount}.", input_message_content=default_message)
            )
        else:
            results.append(
                InlineQueryResultPhoto(f"play_{card}", PLACEHOLDER_IMG, PLACEHOLDER_IMG, title=str(card),
                                        description=f"You have {amount}.", caption=str(card))
            )
    
    return query.answer(results=results, cache_time=0, is_personal=True)



def stop(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if not UnoTelegramGame.in_chat(context, chat):
        return user.send_message(text=f"❌ No game in progress in {chat.title}.")
    
    game = UnoTelegramGame.get_game(context, chat)

    game.cleanup(context)
    return chat.send_message("Game ended.")

    
def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)

if __name__ == "__main__":
    updater = Updater(API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    join_handler = CallbackQueryHandler(join, pattern='join')
    start_game_handler = CallbackQueryHandler(start_game, pattern='start')
    play_inline_handler = InlineQueryHandler(play, pattern='play')

    dispatcher.add_handler(play_inline_handler)
    dispatcher.add_handler(join_handler)
    dispatcher.add_handler(start_game_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stop_handler)

    # dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()