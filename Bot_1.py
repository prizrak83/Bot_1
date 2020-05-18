import telebot as tb
import os
import fitz

f = open('token.txt')
bot = tb.TeleBot(f.read())
tb.apihelper.proxy = {'https': 'socks5://14611055481:U777Vluhz8@orbtl.s5.opennetwork.cc:999'}
files = []


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global files
    print(call.data)
    print(call.data[4:])
    keyboard = tb.types.InlineKeyboardMarkup()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data.startswith('page'):
        page = int(call.data[4:])
        if page == 0:
            for name in files[0:5]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[0:-4], callback_data=name[0:-4]))
            keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='page'+str(page+1)))
        else:
            keyboard.add(tb.types.InlineKeyboardButton(text='<<', callback_data='page'+str(page-1)))
            for name in files[page*5+0:page*5+4]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[0:-4], callback_data=name[0:-4]))
            if len(files)-page+5 < 5:
                keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='page'+str(page+1)))
        bot.send_message(call.message.chat.id, 'список', reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, xps(call.data))


@bot.message_handler(commands=['start'])
def start_message(message):
    global files
    keyboard = tb.types.InlineKeyboardMarkup()
    files = os.listdir('./pass')
    if len(files) < 6:
        for name in files:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[0:-4], callback_data=name[0:-4]))
    else:
        keyboard = tb.types.InlineKeyboardMarkup()
        for name in files[0:5]:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[0:-4], callback_data=name[0:-4]))
        keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='page1'))

    bot.send_message(message.chat.id, 'список', reply_markup=keyboard)


def xps(file_name):
    doc = fitz.open('./pass/'+file_name+".xps")
    password = doc.getPageText(0)
    doc.close()
    return password


bot.polling(none_stop=True, timeout=123)
