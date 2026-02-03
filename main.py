import json
import os
from pathlib import Path
from datetime import datetime
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv # Run 'pip install python-dotenv'

# Load environment variables
load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent / "web" / "config.json"


def load_config_dates() -> tuple[str, str]:
    today = datetime.now().strftime('%Y-%m-%d')
    return today, today
    
    if not CONFIG_PATH.exists():
        return today, today

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        start_date = data.get("startDate") or today
        end_date = data.get("endDate") or today
        return start_date, end_date
    except Exception:
        return today, today

def run_ipo_automation(target_email: str | None = None):
    # Fetch credentials from environment
    token = os.getenv('FINNHUB_TOKEN')
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    target_email = target_email or os.getenv('TARGET_EMAIL')

    # 1. Set Date Range
    start, end = load_config_dates()
    url = f"https://finnhub.io/api/v1/calendar/ipo?from={start}&to={end}&token={token}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        qualified_tickers = []
        ipos = data.get('ipoCalendar', [])

        for ipo in ipos:
            # Condition: (IPO Price * Number of Shares) > USD 200M
            price = float(ipo.get('price') or 0)
            shares = int(ipo.get('numberOfShares') or 0)
            offer_amount = price * shares
            
            if offer_amount > 200_000_000:
                symbol = ipo.get('symbol', 'N/A')
                qualified_tickers.append(f"{symbol} (Offer: ${offer_amount/1e6:.1f}M)")

        # 2. Email Notification Logic
        if qualified_tickers:
            msg = EmailMessage()
            if start == end:
                msg.set_content(f"IPO Alert for {start}:\n\n" + "\n".join(qualified_tickers))
                msg['Subject'] = f"High-Value IPO Alert - {start}"
            else:
                msg.set_content(f"IPO Alert from {start} to {end}:\n\n" + "\n".join(qualified_tickers))
                msg['Subject'] = f"High-Value IPO Alert - {start} to {end}"
            msg['From'] = email_user
            msg['To'] = target_email

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_user, email_pass)
                smtp.send_message(msg)
            print(f"Workflow Complete: Email sent for {len(qualified_tickers)} tickers.")
        else:
            print(f"No IPOs met the $200M threshold for {end}.")

    except Exception as e:
        print(f"Error executing workflow: {e}")

if __name__ == "__main__":
    run_ipo_automation()