
import requests
import asyncio
import logging
import urllib3

from datetime import datetime
from telegram import Bot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==================================================
# CONFIGURATION
# ==================================================

API_URL = "https://prepaid.desco.org.bd/api/unified/customer/getBalance"

API_PARAMS = {
    "accountNo": "41206449",
    "meterNo": "036710006494"
}

TELEGRAM_BOT_TOKEN = "8040802671:AAHyJ_MKzzxKVr0KECIYQNv09Pf0d2OIbWw"
CHAT_ID = "6102069101"

LOW_BALANCE_LIMIT = 100

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==================================================
# SSL CONFIGURATION
# ==================================================

# Temporary workaround for DESCO SSL issues.
# Prefer proper certificate verification when possible.
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ==================================================
# REQUEST SESSION WITH RETRIES
# ==================================================

session = requests.Session()

session.verify = False

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

# ==================================================
# FETCH DESCO BALANCE
# ==================================================

def get_desco_balance():

    try:
        logging.info("Connecting to DESCO API...")

        response = session.get(
            API_URL,
            params=API_PARAMS,
            timeout=(15, 30),
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        logging.info(
            f"DESCO HTTP Status: {response.status_code}"
        )

        data = response.json()

        # Validate API response
        if data.get("code") != 200:
            logging.error(f"DESCO API error: {data}")

            return (
                "❌ DESCO API Error\n\n"
                f"Response: {data}"
            )

        info = data.get("data")

        if not isinstance(info, dict):
            logging.error(f"Invalid API data: {data}")

            return "❌ DESCO API returned empty or invalid data."

        # Extract information
        balance = info.get("balance")
        consumption = info.get(
            "currentMonthConsumption", "N/A"
        )
        reading_time = info.get("readingTime", "N/A")
        account = info.get("accountNo", "N/A")
        meter = info.get("meterNo", "N/A")

        if balance is None:
            return "❌ DESCO balance is missing."

        balance_value = float(balance)

        # Low balance warning
        warning = ""

        if balance_value < LOW_BALANCE_LIMIT:

            warning = (
                "\n\n⚠️ WARNING: LOW BALANCE!\n"
                "Please recharge your DESCO meter soon."
            )

        # Prepare message
        message = (
            "💡 DESCO Balance Update\n\n"
            f"👤 Account: {account}\n"
            f"🔢 Meter: {meter}\n"
            f"💰 Balance: {balance_value:.2f} Tk\n"
            f"📊 Consumption: {consumption} kWh\n"
            f"🕒 Reading Time: {reading_time}"
            f"{warning}\n\n"
            f"📤 Sent at: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        logging.info(
            f"Balance fetched successfully: {balance_value}"
        )

        return message

    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except requests.exceptions.SSLError as e:

        logging.exception("DESCO SSL Error")

        return (
            "❌ DESCO SSL Error\n\n"
            f"Details: {str(e)}"
        )

    except requests.exceptions.Timeout as e:

        logging.exception("DESCO Timeout")

        return (
            "❌ DESCO API Timeout\n\n"
            f"Details: {str(e)}"
        )

    except requests.exceptions.ConnectionError as e:

        logging.exception("DESCO Connection Error")

        return (
            "❌ DESCO Connection Error\n\n"
            f"Details: {str(e)}"
        )

    except requests.exceptions.HTTPError as e:

        logging.exception("DESCO HTTP Error")

        return (
            "❌ DESCO HTTP Error\n\n"
            f"Details: {str(e)}"
        )

    except (ValueError, requests.exceptions.JSONDecodeError) as e:

        logging.exception("Invalid DESCO Response")

        return (
            "❌ Invalid DESCO API Response\n\n"
            f"Details: {str(e)}"
        )

    except Exception as e:

        logging.exception("Unexpected Error")

        return (
            "❌ Unexpected Error\n\n"
            f"Details: {str(e)}"
        )


# ==================================================
# SEND TELEGRAM MESSAGE
# ==================================================

async def send_telegram_message(message):

    try:

        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:

            await bot.send_message(
                chat_id=CHAT_ID,
                text=message
            )

        logging.info(
            "Telegram message sent successfully."
        )

    except Exception:

        logging.exception(
            "Telegram message sending failed."
        )


# ==================================================
# MAIN
# ==================================================

async def main():

    logging.info("Starting DESCO Balance Monitor")

    message = get_desco_balance()

    print("\n" + message + "\n")

    await send_telegram_message(message)

    logging.info("DESCO monitoring completed.")


if __name__ == "__main__":

    asyncio.run(main())
