import telebot as tb
import glob
import fitz
import json


HELP_TEXT = 'Для запроса пароля узла введите \n /list <колличество строк на странице> <имя узла> \n' \
            'если колличество строк не задано то оно равно 5'
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
        page_size = int(call.data[1])
        if call.data[3] == ' ':
            page = int(call.data[2])
            mask = call.data[4:]
        elif call.data[4] == ' ':
            page = int(call.data[2:4])
            mask = call.data[5:]
        else:
            page = int(call.data[2:5])
            mask = call.data[6:]
        files = glob.glob('./pass/*' + mask + '*.*')
        if page == 0:
            for name in files[0:page_size]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
            keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!'+str(page_size)+str(page+1)+' '+mask))
        else:
            keyboard.add(tb.types.InlineKeyboardButton(text='<<', callback_data='!'+str(page_size)+str(page-1)+' '+mask))
            for name in files[page*page_size+0:page*page_size+page_size]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
            if len(files)-(page*page_size) > page_size:
                keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!'+str(page_size)+str(page+1)+' '+mask))
        bot.send_message(call.message.chat.id, 'список', reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, xps(call.data))


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    print(message.chat.id)

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return
    bot.send_message(message.chat.id, HELP_TEXT)


@bot.message_handler(commands=['list'])
def text_message(message):
    global acl
    if message.text[7] != ' ':
        page_size = 5
        mask = message.text[6:]
    elif int(message.text[6]) < 5:
        page_size = 5
        mask = message.text[6:]
    else:
        page_size = int(message.text[6])
        mask = message.text[8:]
    print(mask)
    print(page_size)

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    keyboard = tb.types.InlineKeyboardMarkup()
    files = glob.glob('./pass/*'+mask+'*.*')
    if len(files) < (page_size+1):
        for name in files:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
    else:
        keyboard = tb.types.InlineKeyboardMarkup()
        for name in files[0:page_size]:
            keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
        keyboard.add(tb.types.InlineKeyboardButton(text='>>', callback_data='!'+str(page_size)+'1 '+mask))

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
