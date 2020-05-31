import telebot as tb
import glob
import fitz
import json
import configparser
from time import sleep, time
from multiprocessing import Process
import sqlite3

HELP_TEXT = 'Для запроса пароля узла введите \n /list <колличество строк на странице> <имя узла> \n' \
            'колличество строк задётся в интервале от 5 до 9, если не задано то равно 5\n' \
            'Для запроса админских паролей введите команду /admin_list' \
            'Собщение с паролем удалится через 5 минут'
ADMIN_HELP_TEXT = '/acl_list - список пользователей\n/acl_error - последний не зарегестрированный пользователь\n' \
                  '/acl_add <имя пользователя>- добавление последнего не зарегестрированного пользовател\n' \
                  '/acl_del <id пользователя> - удаление пользователяиз списка доступа\n' \
                  '/acl_save  - сохранение текущего списка доступа в файл'

config = configparser.ConfigParser()
config.read('config.ini')
acl_file = config.get('Settings', 'acl_file')
token_file = config.get('Settings', 'token_file')
proxy_type = config.get('Settings', 'proxy_type')
admin_index = int(config.get('Settings', 'admin_index'))
config.read('proxy.ini')
proxy_address = config.get('Settings', 'proxy_address')

f = open(token_file)
bot = tb.TeleBot(f.read())
f.close()


tb.apihelper.proxy = {proxy_type: proxy_address}

f = open(acl_file, 'r')
acl_user = json.load(f)
f.close()

acl = []
for i in range(len(acl_user)):
    acl.append(acl_user[i][0])

print(acl_user)
last_id_error = None


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
            keyboard.add(tb.types.InlineKeyboardButton(text='>>',
                                                       callback_data='!'+str(page_size)+str(page+1)+' '+mask))
        else:
            keyboard.add(tb.types.InlineKeyboardButton(text='<<',
                                                       callback_data='!'+str(page_size)+str(page-1)+' '+mask))
            for name in files[page*page_size+0:page*page_size+page_size]:
                keyboard.add(tb.types.InlineKeyboardButton(text=name[7:-4], callback_data=name[7:40]))
            if len(files)-(page*page_size) > page_size:
                keyboard.add(tb.types.InlineKeyboardButton(text='>>',
                                                           callback_data='!'+str(page_size)+str(page+1)+' '+mask))
        bot.send_message(call.message.chat.id,
                         'Cтраница '+str(page+1)+' из '+str(len(files)//page_size), reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, xps(call.data))
        add_message_in_list(call.message.message_id+1, call.message.chat.id, int(time())+300)


@bot.message_handler(commands=['acl_error'])
def show_acl_error(message):
    global last_id_error, acl
    if message.chat.id == acl[admin_index]:
        if last_id_error is None:
            bot.send_message(message.chat.id, 'Отсутсвует не зарегестрированный пользователь')
            return
        bot.send_message(message.chat.id, 'Последний не зарегестрированный пользователь '+str(last_id_error))


@bot.message_handler(commands=['acl_add'])
def add_acl(message):
    global last_id_error, acl, acl_user
    user_name = message.text[10:]
    if message.chat.id == acl[admin_index]:
        if last_id_error is None:
            bot.send_message(message.chat.id, 'Отсутсвует не зарегестрированный пользователь')
            return
        if len(user_name) == 0:
            bot.send_message(message.chat.id, 'После команды /acl_add напишите имя пользователя')
            return
        acl.append(last_id_error)
        acl_user.append([last_id_error, user_name])
        show_acl_list(message)
        last_id_error = None
        bot.send_message(message.chat.id, 'для сохранения списка в файл выполните команду /acl_save')


@bot.message_handler(commands=['acl_save'])
def add_acl(message):
    global acl, acl_user, acl_file
    if message.chat.id == acl[admin_index]:
        f = open(acl_file, 'w')
        json.dump(acl_user, f)
        f.close()


@bot.message_handler(commands=['acl_del'])
def acl_delete(message):
    global acl, acl_user
    if message.chat.id == acl[admin_index]:
        del_id = int(message.text[9:])
        if del_id == 0 or not(del_id in acl):
            bot.send_message(message.chat.id, 'Введён не верный id пользователя, проверьте id через команду /acl_list')
            return
        if del_id == message.chat.id:
            bot.send_message(message.chat.id, 'Нельзя удалить администратора')
            return
        i = acl.index(del_id)
        del acl[i]
        del acl_user[i]
        bot.send_message(message.chat.id, 'Пользователь удалён')
        show_acl_list(message)


@bot.message_handler(commands=['acl_list'])
def show_acl_list(message):
    global last_id_error, acl, acl_user
    if message.chat.id == acl[admin_index]:
        acl_list = 'Список зарегестрированных пользователей\n'
        for user_id in acl_user:
            acl_list = acl_list + str(user_id[0])+' '+user_id[1] + '\n'
        bot.send_message(message.chat.id, acl_list)


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    global last_id_error, acl
    print(message.chat.id)
    get_settings()

    if not(message.chat.id in acl):
        last_id_error = message.chat.id
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    bot.send_message(message.chat.id, HELP_TEXT)

    if message.chat.id == acl[admin_index]:
        bot.send_message(message.chat.id, ADMIN_HELP_TEXT)


@bot.message_handler(commands=['admin_list'])
def admin_list(message):
    global acl

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    f = open('AdminGroupPas.txt')
    bot.send_message(message.chat.id, f.read())
    add_message_in_list(message.message_id + 1, message.chat.id, int(time()) + 300)
    f.close()


@bot.message_handler(commands=['list'])
def list_message(message):
    global acl
    message_string = message.text.replace(' ', '')
    if (len(message_string) == 5) or not(message_string[5].isdigit()):
        page_size = 5
        mask = message_string[5:]
    else:
        page_size = int(message_string[5])
        mask = message_string[6:]

    if page_size < 5:
        page_size = 5

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

    bot.send_message(message.chat.id, 'Найдено узлов '+str(len(files)), reply_markup=keyboard)


def xps(filemask):
    fileslist = glob.glob('./pass/'+filemask[0:-4]+'*.*')
    password = ' '
    for filename in fileslist:
        doc = fitz.open(filename)
        password = password + doc.getPageText(0)
        doc.close()
    return password


def get_settings():
    global acl_file, admin_index

    config = configparser.ConfigParser()
    config.read('config.ini')
    acl_file = config.get('Settings', 'acl_file')
    admin_index = int(config.get('Settings', 'admin_index'))


def add_message_in_list(message_id, chat_id, message_time):
    conn = sqlite3.connect("temp.db")
    cursor = conn.cursor()
    entities = (message_id, chat_id, message_time)
    cursor.execute("""INSERT INTO message_list(message_id, chat_id, message_time) VALUES(?, ?, ?) """, entities)
    conn.commit()
    cursor.close()


def delete_message():
    while True:
        sleep_time = 300
        conn = sqlite3.connect("temp.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM message_list')
        message_list = cursor.fetchall()
        for message in message_list:
            if message[3] < int(time()):
                bot.delete_message(message[2], message[1])
                cursor.execute('DELETE FROM message_list WHERE id =:id', {'id': message[0]})
            elif sleep_time > message[3] - int(time()):
                sleep_time = message[3] - int(time())
        conn.commit()
        cursor.close()
        sleep(sleep_time)


if __name__ == "__main__":
    conn_init = sqlite3.connect("temp.db")
    cursor_init = conn_init.cursor()
    try:
        cursor_init.execute("drop table message_list")
    except Exception:
        print(0)
    finally:
        cursor_init.execute("""CREATE TABLE message_list(id integer PRIMARY KEY, message_id integer,
                                chat_id integer, message_time integer)""")

    conn_init.commit()
    cursor_init.close()

    p1 = Process(target=delete_message, args=())
    p1.start()

    while True:
        try:
            bot.polling(none_stop=True, timeout=123)
        except Exception as e:
            print(e)
            sleep(15)
