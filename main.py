import logging
import configparser

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, PhotoSize,
                    InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, 
                        InlineQueryHandler, RegexHandler)

import uno
from uno.card import ColorCard, SpecialCard, WildCard
from uno_telegram import (UnoTelegramGame,UnoTelegramPlayer, GameNotFound, PlayerNotFound,
                            PlayerAlreadyInGame)

config = configparser.ConfigParser()
config.read('config.ini')

API_TOKEN = config['bot']['API_TOKEN']

# TODO: image link dict

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

    text = f"{game.start_text}\n\n`[-- GAME STARTED --]`"
    message.edit_text(text, parse_mode=ParseMode.MARKDOWN)

    cached_image('uno', 'placeholder.png', chat.send_photo,
                caption=str(game.last_card))
    return chat.send_message(text=f"Your turn {game.current_player}.", parse_mode=ParseMode.MARKDOWN,
                                reply_markup=play_markup)

def render_cards(update, context):
    query = update.inline_query
    user = query.from_user

    try:
        player = UnoTelegramPlayer.get_player(context, user)
        
        game = player.game

        if not game.started: raise PlayerNotFound
    except PlayerNotFound:
        return query.answer(results=[], switch_pm_text="❌ You don't seem to be in a game!",
                            switch_pm_parameter="not_in_game", cache_time=0)

    results = player.render_cards()
    
    return query.answer(results=results, cache_time=0, is_personal=True)

def play(update, context):
    user = update.effective_user
    message = update.message

    try:
        player = UnoTelegramPlayer.get_player(context, user)
        
        game = player.game
        chat = game.chat

        if not game.started: raise PlayerNotFound
    except PlayerNotFound:
        return user.send_message(text="❌ You don't seem to be in a game!")

    if not message.chat == chat: return user.send_message(text=f"🚫 You're in a game in {chat.title}!")
    if not player.is_current_player: return user.send_message(text="🚫 Not your turn!")

    (_, color, number) = update.message.text.split(" ", 2)
    card = ColorCard(color, number)

    last_card = game.last_card
    print(card, last_card)
    try:
        game.play(player, card)
    except uno.errors.BadCard: return message.reply_markdown(quote=True, text="nob can't play dat")

    text = f"{player} played {card} against {last_card}"

    cached_image(str(card), 'placeholder.png', chat.send_photo, caption=text, parse_mode=ParseMode.MARKDOWN)    
    return chat.send_message(text=f'Your turn {game.current_player}', parse_mode=ParseMode.MARKDOWN,
                                reply_markup=play_markup)

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

    # omit 'play'
    chosen_card_filter = Filters.regex('^play (red|green|blue|yellow) \d$')
    chosen_special_card_filter = Filters.regex('^play (red|green|blue|yellow) (\+2|skip|reverse)$')
    chosen_wild_card_filter = Filters.regex('^play (\+4|change color)$')

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    join_handler = CallbackQueryHandler(join, pattern='join')
    start_game_handler = CallbackQueryHandler(start_game, pattern='start')
    play_inline_handler = InlineQueryHandler(render_cards, pattern='play')
    chosen_card_handler = MessageHandler(chosen_card_filter, play)
    # chosen_card_handler = ChosenInlineResultHandler(play)
                            # )
    # chosen_wild_card_handler = ChosenInlineResultHandler(play_wildcard,
    #                                 pattern=)

    dispatcher.add_handler(chosen_card_handler)
    dispatcher.add_handler(play_inline_handler)
    # dispatcher.add_handler(chosen_wild_card_handler)
    dispatcher.add_handler(join_handler)
    dispatcher.add_handler(start_game_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stop_handler)

    # dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()