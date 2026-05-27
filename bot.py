import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# TOKEN (Render Environment Variable'dan gelir)
TOKEN = os.getenv("TOKEN")

# ADMIN ID
ADMIN_IDS = [6844787168]  # buraya kendi Telegram ID'ni yaz

# DATABASE
conn = sqlite3.connect("stok.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    stock INTEGER
)
""")

conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍺 Bar Stok Botu\n\n"
        "/urunekle isim miktar\n"
        "/stok isim\n"
        "/satis isim miktar\n"
        "/guncelle isim miktar\n"
        "/liste"
    )


# ADMIN CHECK
def is_admin(user_id):
    return user_id in ADMIN_IDS


# ÜRÜN EKLE
async def urunekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Yetkisiz erişim!")

    try:
        name = context.args[0]
        stock = int(context.args[1])

        cursor.execute(
            "INSERT INTO products (name, stock) VALUES (?, ?)",
            (name, stock)
        )
        conn.commit()

        await update.message.reply_text(f"✅ {name} eklendi: {stock}")

    except:
        await update.message.reply_text("Kullanım: /urunekle kola 50")


# STOK GÖR
async def stok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]

        cursor.execute("SELECT stock FROM products WHERE name=?", (name,))
        result = cursor.fetchone()

        if result:
            await update.message.reply_text(f"📦 {name}: {result[0]}")
        else:
            await update.message.reply_text("Ürün yok.")

    except:
        await update.message.reply_text("Kullanım: /stok kola")


# SATIŞ
async def satis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Yetkisiz erişim!")

    try:
        name = context.args[0]
        amount = int(context.args[1])

        cursor.execute("SELECT stock FROM products WHERE name=?", (name,))
        result = cursor.fetchone()

        if not result:
            return await update.message.reply_text("Ürün yok.")

        new_stock = result[0] - amount

        if new_stock < 0:
            return await update.message.reply_text("Yetersiz stok!")

        cursor.execute(
            "UPDATE products SET stock=? WHERE name=?",
            (new_stock, name)
        )

        conn.commit()

        msg = f"🍻 {amount} {name} satıldı. Yeni stok: {new_stock}"

        if new_stock <= 10:
            msg += "\n⚠️ KRİTİK STOK!"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("Kullanım: /satis kola 5")


# GÜNCELLE
async def guncelle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Yetkisiz erişim!")

    try:
        name = context.args[0]
        stock = int(context.args[1])

        cursor.execute(
            "UPDATE products SET stock=? WHERE name=?",
            (stock, name)
        )

        conn.commit()

        await update.message.reply_text(f"🔄 {name}: {stock}")

    except:
        await update.message.reply_text("Kullanım: /guncelle kola 100")


# LİSTE
async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT name, stock FROM products")
    rows = cursor.fetchall()

    if not rows:
        return await update.message.reply_text("Ürün yok.")

    text = "📋 STOK LİSTESİ\n\n"

    for name, stock in rows:
        icon = "🔴" if stock <= 10 else "🟢"
        text += f"{icon} {name} → {stock}\n"

    await update.message.reply_text(text)


# BOT START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("urunekle", urunekle))
app.add_handler(CommandHandler("stok", stok))
app.add_handler(CommandHandler("satis", satis))
app.add_handler(CommandHandler("guncelle", guncelle))
app.add_handler(CommandHandler("liste", liste))

print("Bot çalışıyor...")

if __name__ == "__main__":
    app.run_polling()
