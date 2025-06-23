from telegram import ReplyKeyboardMarkup
from texts import TEXTS

def keyboard(key, lang):
    return ReplyKeyboardMarkup(TEXTS[key][lang], resize_keyboard=True)

def keyboard_from_data(buttons):
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def keyboard_single_from_menu(menu_key, lang, row_index=-1):
    return ReplyKeyboardMarkup(
        [TEXTS[menu_key][lang][row_index]],
        resize_keyboard=True
    )

def build_main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=TEXTS["menu_main"][lang],
        resize_keyboard=True
    )