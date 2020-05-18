import telebot as tb
import glob
import fitz
import json


f = open('token.txt')
bot = tb.TeleBot(f.read())
f.close()
tb.apihelper.proxy = {'https': 'socks5://14611055481:U777Vluhz8@orbtl.s5.opennetwork.cc:999'}
f = open('access.txt', 'r')
acl = json.load(f)
print(acl)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global acl

    if not(call.message.chat.id in acl):
        bot.send_message(call.message.chat.id, 'Ошибка доступа')
        return

    keyboard = tb.types.InlineKeyboardMarkup()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data.startswith('!'):
        if call.data[2] == ' ':
            page = int(call.data[1])
            mask = call.data[3:]
        elif call.data[3] == ' ':
            page = int(call.data[1:3])
            mask = call.data[4:]
        else:
            page = int(call.data[1:4])
            mask = call.data[5:]
        files = glob.glob('./pass/*' + mask + '*.*')
        if page == 0:
            for name in files[0:5]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
            keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!'+str(page+1)+' '+mask))
        else:
            keyboard.add(tb.types.InlineKeyboardButton(text='<<', callback_data='!'+str(page-1)+' '+mask))
            for name in files[page*5+0:page*5+4]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
            if len(files)-(page*5) > 5:
                keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!'+str(page+1)+' '+mask))
        bot.send_message(call.message.chat.id, 'список', reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, xps(call.data))


@bot.message_handler(commands=['start'])
def start_message(message):
    print(message.chat.id)

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return


@bot.message_handler(commands=['list'])
def text_message(message):
    global acl
    mask = message.text[6:]

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    keyboard = tb.types.InlineKeyboardMarkup()
    files = glob.glob('./pass/*'+mask+'*.*')
    if len(files) < 6:
        for name in files:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
    else:
        keyboard = tb.types.InlineKeyboardMarkup()
        for name in files[0:5]:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
        keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!1 '+mask))

    bot.send_message(message.chat.id, 'список', reply_markup=keyboard)


def xps(filemask):
    fileslist = glob.glob('./pass/'+filemask[0:-4]+'*.*')
    password = ' '
    for filename in fileslist:
        doc = fitz.open(filename)
        password = password + doc.getPageText(0)
        doc.close()
    return password


bot.polling(none_stop=True, timeout=123)
