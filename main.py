import telebot
import settings
import database_work

bot = telebot.TeleBot(settings.__TELEGRAM_TOKEN__, parse_mode=None)
db = database_work.DbWorker()

auth_users = db.get_true_users()


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


bot.polling()
