import requests
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
import io

TOKEN = "7850331876:AAF8_6KdXpvECYzwf-6xfgYuZpjF2fGVmvE"

# Mapping short symbols to CoinGecko IDs
symbol_map = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "ltc": "litecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin"
}

# Simple in-memory portfolio per user (user_id: {coin: amount})
portfolios = {}

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Welcome to Advanced Crypto Bot!\n\n"
        "Commands:\n"
        "/price <symbol> - Get price\n"
        "/top10 - Top 10 coins\n"
        "/chart <symbol> - Price chart\n"
        "/portfolio add <symbol> <amount> - Add coins to portfolio\n"
        "/portfolio view - View your portfolio\n"
        "/help - Show this message"
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price btc")
        return
    user_input = context.args[0].lower()
    coin_id = symbol_map.get(user_input)
    if not coin_id:
        await update.message.reply_text("Invalid coin symbol! Try btc, eth, sol, etc.")
        return
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    response = requests.get(url).json()
    if coin_id in response:
        price = response[coin_id]['usd']
        await update.message.reply_text(f"{user_input.upper()} price is ${price}")
    else:
        await update.message.reply_text("Coin data not found!")

async def top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
    response = requests.get(url).json()
    msg = "🔥 Top 10 Cryptos by Market Cap 🔥\n\n"
    for coin in response:
        msg += f"{coin['market_cap_rank']}. {coin['name']} ({coin['symbol'].upper()}): ${coin['current_price']}\n"
    await update.message.reply_text(msg)

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /chart btc")
        return
    user_input = context.args[0].lower()
    coin_id = symbol_map.get(user_input)
    if not coin_id:
        await update.message.reply_text("Invalid coin symbol! Try btc, eth, sol, etc.")
        return
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    response = requests.get(url).json()

    prices = response.get("prices")
    if not prices:
        await update.message.reply_text("No chart data found.")
        return
    
    # Prepare data for chart
    times = [p[0] for p in prices]  # timestamps
    values = [p[1] for p in prices]  # prices

    plt.figure(figsize=(10,5))
    plt.plot(values, label=f"{user_input.upper()} Price (7d)")
    plt.title(f"{user_input.upper()} Price Chart (7 days)")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)

    # Save plot to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    await update.message.reply_photo(photo=buf)

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text(
            "Portfolio commands:\n"
            "/portfolio add <symbol> <amount>\n"
            "/portfolio view"
        )
        return
    sub_cmd = context.args[0].lower()
    if sub_cmd == "add":
        if len(context.args) != 3:
            await update.message.reply_text("Usage: /portfolio add <symbol> <amount>")
            return
        symbol = context.args[1].lower()
        amount = context.args[2]
        try:
            amount = float(amount)
        except ValueError:
            await update.message.reply_text("Amount must be a number.")
            return
        coin_id = symbol_map.get(symbol)
        if not coin_id:
            await update.message.reply_text("Invalid coin symbol.")
            return
        
        user_port = portfolios.get(user_id, {})
        user_port[coin_id] = user_port.get(coin_id, 0) + amount
        portfolios[user_id] = user_port
        await update.message.reply_text(f"Added {amount} {symbol.upper()} to your portfolio.")
    elif sub_cmd == "view":
        user_port = portfolios.get(user_id)
        if not user_port:
            await update.message.reply_text("Your portfolio is empty.")
            return
        msg = "💼 Your Portfolio:\n"
        total_value = 0
        for coin_id, amt in user_port.items():
            # Get current price
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            data = requests.get(url).json()
            price = data.get(coin_id, {}).get("usd", 0)
            val = amt * price
            total_value += val
            msg += f"{coin_id.capitalize()}: {amt} × ${price} = ${val:.2f}\n"
        msg += f"\nTotal Portfolio Value: ${total_value:.2f}"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Unknown portfolio command.")

# ===== INLINE BUTTONS =====

async def start_with_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Top 10 Coins", callback_data='top10')],
        [InlineKeyboardButton("Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Choose an option below or type commands.\n/start, /price, /top10, /chart, /portfolio",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == 'top10':
        # Simulate sending top10 message
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        response = requests.get(url).json()
        msg = "🔥 Top 10 Cryptos by Market Cap 🔥\n\n"
        for coin in response:
            msg += f"{coin['market_cap_rank']}. {coin['name']} ({coin['symbol'].upper()}): ${coin['current_price']}\n"
        await query.edit_message_text(msg)
    elif data == 'help':
        await query.edit_message_text(
            "Commands:\n"
            "/price <symbol>\n"
            "/top10\n"
            "/chart <symbol>\n"
            "/portfolio add <symbol> <amount>\n"
            "/portfolio view"
        )

# ===== MAIN =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start_with_buttons))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("top10", top10))
app.add_handler(CommandHandler("chart", chart))
app.add_handler(CommandHandler("portfolio", portfolio))
app.add_handler(CallbackQueryHandler(button_handler))

print("Advanced Crypto Bot running...")
app.run_polling()
