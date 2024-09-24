import telebot
import sqlite3
import re

# Replace with your actual API token
API_TOKEN = '7594782829:AAFM9zaEblSxSnMWrVLyjsmXBieU_pfEXxQ'

# ID чата, в котором бот должен работать
TARGET_CHAT_ID = -1002208229823  # Замените на ваш ID чата

# ID пользователя, который может выдавать админки
SUPER_ADMIN_ID = 1971188182  # Замените на нужный ID

bot = telebot.TeleBot(API_TOKEN)

# Initialize the database
conn = sqlite3.connect('rules.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS rules (
                  id INTEGER PRIMARY KEY,
                  text TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
                  user_id INTEGER PRIMARY KEY)''')
conn.commit()

@bot.message_handler(func=lambda message: message.chat.id != TARGET_CHAT_ID)
def ignore_other_chats(message):
    # Игнорировать сообщения из других чатов
    return

@bot.message_handler(func=lambda message: message.chat.id == TARGET_CHAT_ID and message.text.startswith('//правила'))
def show_rules(message):
    cursor.execute("SELECT id, text FROM rules ORDER BY id")
    rules = cursor.fetchall()
    if rules:
        response = "Правила чата:\n" + "\n".join([f"{rule[0]}. {rule[1]}" for rule in rules])
    else:
        response = "правил нету анархия ура"
    bot.reply_to(message, response)

def is_admin(user_id):
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None or user_id == SUPER_ADMIN_ID

@bot.message_handler(func=lambda message: message.chat.id == TARGET_CHAT_ID and message.text.lower() == 'админы')
def show_admins(message):
    cursor.execute("SELECT user_id FROM admins")
    admins = cursor.fetchall()
    if not admins:
        bot.reply_to(message, "ура анархия")
        return

    admin_list = []
    for admin in admins:
        user_id = admin[0]
        try:
            user = bot.get_chat_member(TARGET_CHAT_ID, user_id).user
            username = user.username or "без юзернейма"
            full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
            admin_list.append(f"{full_name} (@{username}) - {user_id}")
        except:
            admin_list.append(f"Неизвестный пользователь - {user_id}")

    response = "Администраторы чата:\n" + "\n".join(admin_list)
    bot.reply_to(message, response)

@bot.message_handler(commands=['+админ'])
def add_admin(message):
    user_id = message.from_user.id
    if user_id != SUPER_ADMIN_ID:
        bot.reply_to(message, "нехачу")
        return

    try:
        parts = message.text.split()
        if len(parts) == 2:
            username = parts[1].strip('@')
            user_info = bot.get_chat_member(TARGET_CHAT_ID, username)
            new_admin_id = user_info.user.id
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
            conn.commit()
            bot.reply_to(message, f"раб системы {username} (ID: {new_admin_id}) добавлен в администраторы")
        else:
            bot.reply_to(message, "нехачу")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.chat.id == TARGET_CHAT_ID and message.text.startswith('+правило'))
def add_rule(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "только рабы системы могут изменять")
        return

    try:
        rule_text = re.match(r'^\+правило\s+(.+)', message.text, re.DOTALL)
        if rule_text:
            rule_text = rule_text.group(1).strip()
            if rule_text:
                cursor.execute("INSERT INTO rules (text) VALUES (?)", (rule_text,))
                # Перенумерация оставшихся правил после добавления
                cursor.execute("SELECT id FROM rules ORDER BY id")
                remaining_rules = cursor.fetchall()
                for new_id, (old_id,) in enumerate(remaining_rules, start=1):
                    cursor.execute("UPDATE rules SET id = ? WHERE id = ?", (new_id, old_id))
                conn.commit()
                bot.reply_to(message, "Правило добавлено")
            else:
                bot.reply_to(message, "Пожалуйста, сходите нахуй")
        else:
            bot.reply_to(message, "Пожалуйста, еще раз")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.chat.id == TARGET_CHAT_ID and message.text.startswith('-правило'))
def delete_rule(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "только рабы системы могут изменять")
        return

    try:
        parts = message.text.split()
        if len(parts) == 2 and parts[1].isdigit():
            rule_id = int(parts[1])
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()

            # Перенумерация оставшихся правил после удаления
            cursor.execute("SELECT id FROM rules ORDER BY id")
            remaining_rules = cursor.fetchall()
            for new_id, (old_id,) in enumerate(remaining_rules, start=1):
                cursor.execute("UPDATE rules SET id = ? WHERE id = ?", (new_id, old_id))
            conn.commit()

            bot.reply_to(message, "Правило удалено")
        elif len(parts) == 2 and parts[1] == 'все':
            cursor.execute("DELETE FROM rules")
            conn.commit()
            bot.reply_to(message, "Все правила удалены плаке плаке...")
        else:
            bot.reply_to(message, "Пожалуйста, научитесь пользоваться командами")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

bot.polling()
