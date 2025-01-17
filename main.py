import re
from decimal import Decimal

import telebot
from telebot import types

import database_work
import settings
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
        bot.send_message(message.from_user.id,
                         'Доступа нет, чтобы получить доступ, нужно использовать команду\n/auth <ТВОЙ КЛЮЧ БЕЗ КАВЫЧЕК>')


@bot.message_handler(commands=['auth'])
def auth_user(message):
    global auth_users
    if message.from_user.id in auth_users:
        bot.send_message(message.from_user.id, 'У вас уже есть доступ')
        return

    if len(message.text.split(' ')) != 2:
        bot.send_message(message.from_user.id, 'Что-то пошло не так, напиши /start и следуй инструкциям')
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


@bot.message_handler(commands=['stocks_list'])
def get_stocks(message):
    # TODO: Ченить сделать
    aa = Account.get_list_stocks()
    bot.send_message(message.from_user.id, str(aa))


@bot.message_handler(commands=['search_by_ticker'])
def search_by_ticker(message):
    bot.send_message(message.from_user.id, 'Введите тикер ценной бумаги')
    bot.register_next_step_handler(message, ticker_search)


def ticker_search(message):
    ticker = message.text
    response = Account.search_by_ticker(ticker)
    bot.send_message(message.from_user.id, response)


@bot.message_handler(commands=['buy_by_ticker'])
def buy_ticker(message):
    bot.send_message(message.from_user.id, 'Введите тикер ценной бумаги')
    bot.register_next_step_handler(message, show_price_list)


def show_price_list(message):
    ans = Account.show_price_list(message.text)
    global ticker
    ticker = message.text
    if not ans:
        bot.send_message(message.from_user.id, 'По такому тикеру ничего не удалось найти')
    else:
        price_list = "{}\n".format(ans[2])
        markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)

        for price, cnt in ans[0]:
            pr = '{0} {1}'.format(price, ans[1])
            price_list += pr + '\n'
            markup.add(types.KeyboardButton(pr))
        price_list += 'Введите свою цену покупки, или укажите рыночную'
        markup.add(types.KeyboardButton('Отмена покупки'))
        bot.send_message(message.from_user.id, price_list, reply_markup=markup)
        bot.register_next_step_handler(message, set_price)


def set_price(message):
    if message.text == 'Отмена покупки':
        bot.send_message(message.from_user.id, 'Процесс покупки прерван')
        return
    global stock_price, stock_cnt
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))

    try:
        stock_price = Decimal(message.text.split(' ')[0])
    except Exception:
        bot.send_message(message.from_user.id, 'Процесс покупки прерван, произошла ошибка')
        return

    bot.send_message(message.from_user.id, 'Введите количество лотов', reply_markup=markup)
    bot.register_next_step_handler(message, set_lots_and_buy)


def set_lots_and_buy(message):
    if message == 'Отмена':
        bot.send_message(message.from_user.id, 'Процесс покупки прерван')
        return

    global ticker
    markup = types.ReplyKeyboardRemove(selective=False)
    global stock_price, stock_cnt
    try:
        stock_cnt = int(message.text)
    except Exception:
        bot.send_message(message.from_user.id, 'Процесс покупки прерван', reply_markup=markup)
        return

    status = Account.buy_by_ticker(stock_price, stock_cnt)
    if status:
        bot.send_message(message.from_user.id, 'Покупка совершена', reply_markup=markup)
        db.buy_stocks(message.from_user.id, ticker, stock_price, stock_cnt)
    else:
        bot.send_message(message.from_user.id, 'Недостаточно средств', reply_markup=markup)


@bot.message_handler(commands=['my_stocks'])
def my_stocks(message):
    portfolio = Account.get_my_stocks()
    msg = '{}\n'.format('Список ваших акций')
    for stock in portfolio:
        msg += '{0} ({1}): {2} лотов ({3} шт.)\n'.format(stock['name'], stock['ticker'], stock['lots'], stock['cnt'])
    msg += '-' * 10 + '\n'
    spent = db.get_stocks(message.from_user.id)
    personal_account_now = Account.get_difference(spent)
    msg += 'Доход: ' + str(personal_account_now[0]) + ' рублей\n'
    msg += str(personal_account_now[0] / personal_account_now[1]['USD000UTSTOM']) + ' долларов\n'
    msg += str(personal_account_now[0] / personal_account_now[1]['EUR_RUB__TOM']) + ' евро\n'
    bot.send_message(message.from_user.id, msg)


@bot.message_handler(commands=['sell_stocks'])
def sell_stocks(message):
    portfolio = Account.get_my_stocks()
    print(portfolio)
    ticker_list = [i['ticker'] for i in portfolio]
    cnt = {i['ticker']: (i['lots'], i['cnt']) for i in portfolio}
    prices = Account.get_price_by_tickets(ticker_list)
    help_info = {'portfolio': portfolio, 'prices': prices, 'cnt': cnt}
    msg = ''
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for ticker_, item in prices.items():
        msg += '{0} ({1}): {2} ({3} лота / {4} шт.)\n'.format(item[1], ticker_, item[0], cnt[ticker_][0], cnt[ticker_][1])
        markup.add(types.KeyboardButton(ticker_))
    msg += 'Выберете акции, которые хотите продать'
    markup.add(types.KeyboardButton('Отмена'))
    bot.send_message(message.from_user.id, msg, reply_markup=markup)
    bot.register_next_step_handler(message, choose_cnt, help_info)


def choose_cnt(message, help_info):
    ticker = message.text
    markup = types.ReplyKeyboardRemove(selective=False)
    if ticker == 'Отмена':
        bot.send_message(message.from_user.id, 'Процесс продажи отменен', reply_markup=markup)
        return
    elif ticker not in help_info['cnt']:
        bot.send_message(message.from_user.id, 'Неправильный тикер', reply_markup=markup)
        return
    help_info['ticker'] = ticker
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    bot.send_message(message.from_user.id, 'Сколько лотов хотите продать?', reply_markup=markup)
    bot.register_next_step_handler(message, sell_stocks_finally, help_info)


def sell_stocks_finally(message, help_info):
    markup = types.ReplyKeyboardRemove(selective=False)
    if message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Процесс продажи отменен', reply_markup=markup)
        return
    try:
        num = int(message.text)
    except Exception as e:
        print(e)
        bot.send_message(message.from_user.id, 'Произошла ошибка', reply_markup=markup)
        return
    if help_info['cnt'][help_info['ticker']][0] < num:
        bot.send_message(message.from_user.id, 'Введено число, превышаюшее число лотов', reply_markup=markup)
        return
    # def sell_stocks(self, ticker_, cnt_now, cnt_was, price):
    # тут ошибка
    Account.sell_stocks(help_info['ticker'], help_info['cnt'][0] - num, help_info['cnt'][0], help_info['prices'][help_info['ticker']][0])
    bot.send_message(message.from_user.id, 'Гавно на продажу', reply_markup=markup)


@bot.message_handler(commands=['test'])
def test(message):
    Account.test()

    # a = SandboxSetCurrencyBalanceRequest(balance=Decimal('100.0'), currency=SandboxCurrency.rub)
    # client.set_sandbox_currencies_balance(a)


bot.polling()
