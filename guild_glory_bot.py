import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)

# ----------------- CONFIGURATION ----------------- #
BOT_TOKEN = "9253771868:AAH3K24aU-tS65eYUkuIIRqWlCJjxKSflmI"
ADMIN_TELEGRAM_ID = 8241986368  # তোমার টেলিগ্রাম আইডি (মাস্টার অ্যাডমিন)

# ----------------- DATABASE SETUP ----------------- #
def init_db():
    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            player_id TEXT PRIMARY KEY,
            player_name TEXT,
            glory INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----------------- UI TEMPLATES & HANDLERS ----------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "⚡ **[ SYSTEM CORE: ONLINE ]** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **F R E E  F I R E  E L I T E  G U I L D**\n"
        "💎 *Glory Management Command Center*\n\n"
        "স্বাগতম কমান্ডার! গিল্ডের পারফরম্যান্স ট্র্যাক করতে নিচের প্রিমিয়াম বাটনগুলোতে ট্যাপ করুন অথবা কমান্ড ব্যবহার করুন:\n\n"
        "• `/addmember <ID> <Name>` ➔ মেম্বার রেজিস্টার\n"
        "• `/addglory <ID> <Points>` ➔ গ্লোরি পয়েন্ট যোগ\n"
        "• `/leaderboard` ➔ সেরা খেলোয়াড়দের তালিকা\n"
        "• `/status <ID>` ➔ প্লেয়ার প্রোফাইল কার্ড"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏆 Top Leaderboard", callback_data="cb_leaderboard"),
         InlineKeyboardButton("🛡️ Guild Info", callback_data="cb_stats")],
        [InlineKeyboardButton("⚡ Quick Help & Commands", callback_data="cb_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cb_leaderboard":
        await leaderboard_callback(query)
    elif query.data == "cb_stats":
        conn = sqlite3.connect('guild_glory_elite.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*), SUM(glory) FROM members')
        count, total_glory = cursor.fetchone()
        conn.close()
        
        total_glory = total_glory if total_glory else 0
        stats_text = (
            f"📊 **ELITE GUILD SYSTEM STATS** 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Total Members:** `{count if count else 0}`\n"
            f"⚡ **Total Guild Glory:** `{total_glory}` Points\n"
            f"🟢 **Server Status:** Optimal & Secure\n"
            f"👑 **Guild Master:** Parvez"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="cb_help")]]
        await query.edit_message_text(stats_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "cb_help":
        await start(update, context)

# মেম্বার যুক্ত করার প্রিমিয়াম কমান্ড
async def add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ **ACCESS DENIED:** এই কমান্ড ব্যবহারের অনুমতি শুধু গিল্ড মাস্টারের আছে!")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ **Format Error!**\nব্যবহার করুন: `/addmember <Player_ID> <Name>`", parse_mode="Markdown")
        return
    
    player_id = context.args[0]
    player_name = " ".join(context.args[1:])

    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO members (player_id, player_name, glory) VALUES (?, ?, 0)', (player_id, player_name))
        conn.commit()
        await update.message.reply_text(
            f"✅ **NEW RECRUIT ENROLLED!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Name:** {player_name}\n"
            f"🆔 **ID:** `{player_id}`\n"
            f"🌟 **Status:** Ready for Battle", parse_mode="Markdown"
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ এই প্লেয়ার আইডি ইতিমধ্যে ডাটাবেসে নিবন্ধিত আছে!")
    finally:
        conn.close()

# গ্লোরি পয়েন্ট যোগ করার প্রিমিয়াম কমান্ড
async def add_glory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ **ACCESS DENIED:** গ্লোরি আপডেট করার অধিকার শুধু গিল্ড মাস্টারের রয়েছে!")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ **Format Error!**\nব্যবহার করুন: `/addglory <Player_ID> <Glory_Amount>`", parse_mode="Markdown")
        return

    player_id = context.args[0]
    try:
        glory_to_add = int(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ গ্লোরির পরিমাণ অবশ্যই একটি সংখ্যা হতে হবে!")
        return

    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    cursor.execute('SELECT glory, player_name FROM members WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()

    if row:
        current_glory, name = row
        new_glory = current_glory + glory_to_add
        cursor.execute('UPDATE members SET glory = ? WHERE player_id = ?', (new_glory, player_id))
        conn.commit()
        
        success_msg = (
            f"⚡ **GLORY SYNCED SUCCESSFULLY!** ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Warrior:** {name}\n"
            f"📈 **Added:** `+{glory_to_add}` Points\n"
            f"💎 **New Total Glory:** `{new_glory}`"
        )
        await update.message.reply_text(success_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ **Error:** এই আইডি সিস্টেমে পাওয়া যায়নি! আগে `/addmember` দিয়ে যুক্ত করুন।", parse_mode="Markdown")
    
    conn.close()

# লিডারবোর্ড দেখার প্রিমিয়াম কমান্ড
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, player_id, glory FROM members ORDER BY glory DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📊 বর্তমানে গিল্ডে কোনো মেম্বারের ডেটা এন্ট্রি করা হয়নি!")
        return

    lb_text = "🏆 **ELITE GUILD GLORY LEADERBOARD** 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, (name, p_id, glory) in enumerate(rows, 1):
        if idx == 1:
            medal = "👑 [RANK 1]"
        elif idx == 2:
            medal = "🥈 [RANK 2]"
        elif idx == 3:
            medal = "🥉 [RANK 3]"
        else:
            medal = f"🔹 [RANK {idx}]"
            
        lb_text += f"{medal} **{name}**\n   ┗ ID: `{p_id}` | ⚡ Glory: **{glory}**\n\n"

    await update.message.reply_text(lb_text, parse_mode="Markdown")

async def leaderboard_callback(query):
    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, player_id, glory FROM members ORDER BY glory DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await query.edit_message_text("📊 বর্তমানে গিল্ডে কোনো মেম্বারের ডেটা এন্ট্রি করা হয়নি!")
        return

    lb_text = "🏆 **ELITE GUILD GLORY LEADERBOARD** 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, (name, p_id, glory) in enumerate(rows, 1):
        medal = "👑 [1]" if idx == 1 else "🥈 [2]" if idx == 2 else "🥉 [3]" if idx == 3 else f"🔹 [{idx}]"
        lb_text += f"{medal} **{name}**\n   ┗ ID: `{p_id}` | ⚡ Glory: **{glory}**\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="cb_help")]]
    await query.edit_message_text(lb_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# একক স্ট্যাটাস কার্ড
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ **Format Error!**\nব্যবহার করুন: `/status <Player_ID>`", parse_mode="Markdown")
        return

    player_id = context.args[0]
    conn = sqlite3.connect('guild_glory_elite.db')
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, glory FROM members WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        name, glory = row
        card_text = (
            f"🛡️ **VIP PLAYER IDENTITY CARD** 🛡️\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Gamer Name:** {name}\n"
            f"🆔 **Account ID:** `{player_id}`\n"
            f"⚡ **Total Glory:** `{glory}` Points\n"
            f"🟢 **Guild Standing:** Verified Elite"
        )
        await update.message.reply_text(card_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ এই আইডি দিয়ে কোনো মেম্বার খুঁজে পাওয়া যায়নি!", parse_mode="Markdown")

# ----------------- MAIN RUNNER ----------------- #
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmember", add_member))
    app.add_handler(CommandHandler("addglory", add_glory))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Elite Guild Glory Bot successfully booted up...")
    app.run_polling()