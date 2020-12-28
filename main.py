import json
from decimal import Decimal
import re
import telebot
from telebot import types
from tinvest import SandboxRegisterRequest, SandboxSetCurrencyBalanceRequest, SandboxCurrency, BrokerAccountType, \
    UserAccount

import settings
import database_work
import tinvest

from user import User

bot = telebot.TeleBot(settings.__TELEGRAM_TOKEN__, parse_mode=None)
db = database_work.DbWorker()

auth_users = db.get_true_users()

Account = User()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id in auth_users:
        bot.send_message(message.from_user.id, 'Привет, у тебя есть доступ')
    else:
        bot.send_message(message.from_user.id, 'Доступа нет')


@bot.message_handler(commands=['auth'])
def auth_user(message):
    global auth_users
    if message.from_user.id in auth_users:
        bot.send_message(message.from_user.id, 'У вас уже есть доступ')
        return

    key = message.text.split(' ')[1]
    if key in settings.__ACCESS_KEYS__:
        db.add_user(message.from_user.id)
        auth_users = db.get_true_users()
        bot.send_message(message.from_user.id, 'Доступ разрешен')
    else:
        bot.send_message(message.from_user.id, 'Неверный ключ')


@bot.message_handler(commands=['top_up_balance'])
def top_up_balance(message):
    global auth_users
    if message.from_user.id not in auth_users:
        bot.send_message(message.from_user.id, 'У вас нет доступа')
        return
    else:
        markup = types.ReplyKeyboardMarkup(row_width=3)
        itembtn1 = types.KeyboardButton('70000 rub')
        itembtn2 = types.KeyboardButton('800 eur')
        itembtn3 = types.KeyboardButton('1000 usd')
        markup.add(itembtn1, itembtn2, itembtn3)
        bot.send_message(message.from_user.id, 'Выберите сумму начисления, или введите ее сами', reply_markup=markup)
        bot.register_next_step_handler(message, set_sum)


def set_sum(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    if re.match(r"[0-9]{1,} [a-zA-Z]{3}", message.text):
        sum, curr = message.text.split(' ')
        Account.top_up_balance(sum, curr)
        bot.send_message(message.from_user.id, 'Начислено ✅', reply_markup=markup)
        if False:
            db.top_up(message.from_user.id, message.text)
    else:
        bot.send_message(message.from_user.id, 'Ошибка ⛔️', reply_markup=markup)


@bot.message_handler(commands=['balance'])
def get_balance(message):
    d = Account.get_balance()
    msg = 'На нашем счету:\n'
    for curr, sum in d.items():
        msg += '{0} {1}\n'.format(sum, curr)
    bot.send_message(message.from_user.id, msg)


@bot.message_handler(commands=['test'])
def test(message):
    pass

    # a = SandboxSetCurrencyBalanceRequest(balance=Decimal('100.0'), currency=SandboxCurrency.rub)
    # client.set_sandbox_currencies_balance(a)


bot.polling()
