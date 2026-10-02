import requests
from telegram import Bot
import asyncio
from datetime import datetime
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- DESCO API Info ---
API_URL = "https://prepaid.desco.org.bd/api/unified/customer/getBalance?accountNo=41206449&meterNo=036710006494"


# --- Telegram Bot Info ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8040802671:AAHyJ_MKzzxKVr0KECIYQNv09Pf0d2OIbWw")
CHAT_ID = os.getenv("CHAT_ID", "6102069101")

def get_desco_balance():
    try:
        response = requests.get(API_URL, verify=False, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        
        data = response.json()
        
        # Handle None or missing 'data' key
        info = data.get("data")
        if info is None:
            # Log the actual response for debugging
            print(f"API returned no data. Full response: {data}")
            return "❌ Error: Unable to fetch DESCO balance. API returned no data."
        
        balance = info.get("balance", "N/A")
        consumption = info.get("currentMonthConsumption", "N/A")
        reading_time = info.get("readingTime", "N/A")
        account = info.get("accountNo", "N/A")
        meter = info.get("meterNo", "N/A")

    warning = ""

    try:
        balance_value = float(balance)

        if balance_value < 100:
            warning = (
                "\n⚠️ *WARNING: LOW BALANCE!*\n"
                "Please recharge soon.\n"
        )

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return f"❌ Error: Failed to connect to DESCO API: {str(e)}"
    except ValueError as e:
        print(f"JSON parsing failed: {e}")
        return "❌ Error: Invalid response format from DESCO API"
    message = (
        "💡 *DESCO Balance Update*\n\n"
        f"👤 Account: `{account}`\n"
        f"🔢 Meter: `{meter}`\n"
        f"💰 Balance: *{balance} Tk*\n"
        f"📊 Consumption: {consumption} kWh\n"
        f"🕒 Reading Time: {reading_time}\n"
        f"{warning}\n"
        f"📤 Sent at: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    return message

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

if __name__ == "__main__":
    message = get_desco_balance()
    asyncio.run(send_telegram_message(message))
    print("✅ Telegram message sent!")
