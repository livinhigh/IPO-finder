# IPO Watchlist

Minimal web UI + FastAPI service to collect subscriber emails and send IPO alerts based on the configured date range.

## Features
- Minimal black/white UI to submit an email
- In-memory subscriber list (singleton store)
- Scheduled daily run using `triggerTime` from web/config.json
- Manual run endpoint to send alerts to all subscribers

## Project Structure
- api.py: FastAPI app and scheduler
- main.py: IPO fetch + email sender
- models/: request and subscriber store models
- web/: UI assets and configuration

## Configuration
Edit web/config.json:
- startDate: YYYY-MM-DD
- endDate: YYYY-MM-DD
- triggerTime: HH:MM (24h)

The UI converts `triggerTime` to 12h format.

## Install
```bash
pip install -r requirements.txt
```

## Run the API
```bash
uvicorn api:app --reload
```

Open the UI at:
http://localhost:8000/

## Endpoints
- POST /subscribe
  - body: { "email": "you@example.com" }
  - response: success or already subscribed

- POST /run
  - runs the alert for all subscribers

## Environment Variables
Set these for email delivery:
- FINNHUB_TOKEN
- EMAIL_USER
- EMAIL_PASS
- TARGET_EMAIL (optional fallback)
