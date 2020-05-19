import telebot as tb
import glob
import fitz
import json


HELP_TEXT = 'Для запроса пароля узла введите \n /list <колличество строк на странице> <имя узла> \n' \
            'колличество строк задётся в интервале от 5 до 9, если не задано то равно 5\n' \
            'Для запроса админских паролей введите команду /admin_list'
ADMIN_HELP_TEXT = '/acl_list - список пользователей\n/acl_error - последний не зарегестрированный пользователь\n' \
                  '/acl_add <имя пользователя>- добавление последнего не зарегестрированного пользовател\n' \
                  '/acl_del <id пользователя> - удаление пользователяиз списка доступа\n' \
                  '/acl_save  - сохранение текущего списка доступа в файл'

ACL_FILE = 'access2.txt'
ADMIN_INDEX = 0
f = open('token.txt')
bot = tb.TeleBot(f.read())
f.close()

tb.apihelper.proxy = {'https': 'socks5://14611055481:U777Vluhz8@orbtl.s5.opennetwork.cc:999'}

f = open(ACL_FILE, 'r')
acl_user = json.load(f)
f.close()

acl = []
for i in range(len(acl_user)):
    acl.append(acl_user[i][0])

print(acl_user)
print(acl)
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


@bot.message_handler(commands=['acl_error'])
def show_acl_error(message):
    global last_id_error, acl
    if message.chat.id == acl[ADMIN_INDEX]:
        bot.send_message(message.chat.id, 'Последний не зарегестрированный пользователь'+str(last_id_error))


@bot.message_handler(commands=['acl_add'])
def add_acl(message):
    global last_id_error, acl, acl_user
    user_name = message.text[10:]
    if message.chat.id == acl[ADMIN_INDEX]:
        if last_id_error is None:
            bot.send_message(message.chat.id, 'Отсутсвует не залогиненный пользователь')
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
    global acl, acl_user, ACL_FILE
    if message.chat.id == acl[ADMIN_INDEX]:
        f = open(ACL_FILE, 'w')
        json.dump(acl_user, f)
        f.close()


@bot.message_handler(commands=['acl_del'])
def acl_delete(message):
    global acl, acl_user
    if message.chat.id == acl[ADMIN_INDEX]:
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
        show_acl_list(message)


@bot.message_handler(commands=['acl_list'])
def show_acl_list(message):
    global last_id_error, acl, acl_user
    if message.chat.id == acl[ADMIN_INDEX]:
        acl_list = 'Список зарегестрированных пользователей\n'
        for user_id in acl_user:
            acl_list = acl_list + str(user_id[0])+' '+user_id[1] + '\n'
        bot.send_message(message.chat.id, acl_list)


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    global last_id_error, acl
    print(message.chat.id)

    if not(message.chat.id in acl):
        last_id_error = message.chat.id
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return
    bot.send_message(message.chat.id, HELP_TEXT)
    if message.chat.id == acl[ADMIN_INDEX]:
        bot.send_message(message.chat.id, ADMIN_HELP_TEXT)


@bot.message_handler(commands=['admin_list'])
def admin_list(message):
    global acl

    if not(message.chat.id in acl):
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    f = open('AdminGroupPas.txt')
    bot.send_message(message.chat.id, f.read())
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


bot.polling(none_stop=True, timeout=123)
