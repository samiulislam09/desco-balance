
import requests
import asyncio
import os
import logging

from datetime import datetime
from telegram import Bot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- CONFIGURATION ----------------

API_URL = (
    "https://prepaid.desco.org.bd/api/unified/customer/getBalance"
    "?accountNo=41206449&meterNo=036710006494"
)

TELEGRAM_BOT_TOKEN = "8040802671:AAHyJ_MKzzxKVr0KECIYQNv09Pf0d2OIbWw"
CHAT_ID = "6102069101"

LOW_BALANCE_LIMIT = 100

# ---------------- LOGGING ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- REQUEST SESSION ----------------

session = requests.Session()

retry_strategy = Retry(
    total=4,
    connect=4,
    read=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    respect_retry_after_header=True
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)
session.mount("http://", adapter)

# ---------------- DESCO API ----------------

def get_desco_balance():

    try:
        logging.info("Fetching DESCO balance...")

        response = session.get(
            API_URL,
            timeout=(10, 30),
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        data = response.json()

        # Validate API response
        if data.get("code") != 200:
            logging.error(f"DESCO API error: {data}")
            return "❌ DESCO API returned an unsuccessful response."

        info = data.get("data")

        if not isinstance(info, dict):
            logging.error(f"Invalid API data: {data}")
            return "❌ DESCO API returned empty or invalid data."

        balance = info.get("balance")
        consumption = info.get("currentMonthConsumption", "N/A")
        reading_time = info.get("readingTime", "N/A")
        account = info.get("accountNo", "N/A")
        meter = info.get("meterNo", "N/A")

        if balance is None:
            return "❌ DESCO balance is missing from API response."

        balance_value = float(balance)

        # Low balance warning
        warning = ""

        if balance_value < LOW_BALANCE_LIMIT:
            warning = (
                "\n\n⚠️ WARNING: LOW BALANCE!\n"
                "Please recharge your DESCO meter soon."
            )

        # Prepare Telegram message
        message = (
            "💡 DESCO Balance Update\n\n"
            f"👤 Account: {account}\n"
            f"🔢 Meter: {meter}\n"
            f"💰 Balance: {balance_value:.2f} Tk\n"
            f"📊 Consumption: {consumption} kWh\n"
            f"🕒 Reading Time: {reading_time}"
            f"{warning}\n\n"
            f"📤 Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        logging.info(f"Balance fetched successfully: {balance_value}")

        return message

    except requests.exceptions.Timeout:
        logging.error("DESCO API request timed out.")
        return "❌ DESCO API timeout. Please try again later."

    except requests.exceptions.ConnectionError as e:
        logging.error(f"DESCO connection error: {e}")
        return "❌ Unable to connect to DESCO API."

    except requests.exceptions.HTTPError as e:
        logging.error(f"DESCO HTTP error: {e}")
        return f"❌ DESCO HTTP error: {e}"

    except ValueError as e:
        logging.error(f"Invalid JSON or balance value: {e}")
        return "❌ Invalid response received from DESCO API."

    except Exception as e:
        logging.exception("Unexpected error")
        return f"❌ Unexpected error: {str(e)}"


# ---------------- TELEGRAM ----------------

async def send_telegram_message(message):

    try:
        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:

            await bot.send_message(
                chat_id=CHAT_ID,
                text=message
            )

        logging.info("Telegram message sent successfully.")

    except Exception as e:
        logging.exception(f"Telegram sending failed: {e}")


# ---------------- MAIN ----------------

async def main():

    message = get_desco_balance()

    await send_telegram_message(message)


if __name__ == "__main__":

    asyncio.run(main())
