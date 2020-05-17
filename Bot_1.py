import telebot as tb
import os
import fitz

f = open('token.txt')
bot = tb.TeleBot(f.read())
tb.apihelper.proxy = {'https':'socks5://14611055481:U777Vluhz8@orbtl.s5.opennetwork.cc:999'}


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    bot.send_message(call.message.chat.id, xps(call.data))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['start'])
def start_message(message):
    files = os.listdir('./pass')
    keyboard = tb.types.InlineKeyboardMarkup()
    for name in files:
        keyboard.add(tb.types.InlineKeyboardButton(text=name[0:-4], callback_data=name[0:-4]))

    bot.send_message(message.chat.id, 'список', reply_markup=keyboard)


def xps(file_name):
    print('./pass/'+file_name+".xps")
    doc = fitz.open('./pass/'+file_name+".xps")
    password = doc.getPageText(0)
    doc.close()
    return password


bot.polling(none_stop=True, timeout=123)