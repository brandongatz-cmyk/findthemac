# FindTheMac — Apple Refurbished Product Alert System

Monitors the [Apple Refurbished Store](https://www.apple.com/shop/refurbished) and sends you **email** and **SMS text message** alerts when previously unavailable products come back in stock or new listings appear.

## How It Works

1. **Scrapes** Apple's refurbished product pages and extracts structured product data
2. **Tracks** product availability over time in a local JSON database
3. **Detects** when new products appear or previously unavailable items return
4. **Filters** alerts based on your criteria (category, keywords, price range)
5. **Notifies** you via email (SMTP) and SMS (Twilio)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `SMTP_HOST` | SMTP server hostname (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USERNAME` | Your email login |
| `SMTP_PASSWORD` | Your email password or app-specific password |
| `EMAIL_FROM` | Sender email address |
| `EMAIL_TO` | Recipient email address |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Your Twilio phone number (e.g. `+1234567890`) |
| `SMS_TO_NUMBER` | Recipient phone number (e.g. `+1234567890`) |
| `CHECK_INTERVAL_MINUTES` | How often to check (default: `15`) |
| `CATEGORIES` | Comma-separated categories to monitor |

> **Gmail users:** You'll need an [App Password](https://support.google.com/accounts/answer/185833) — regular passwords won't work with 2FA enabled.

### 3. Set up alert filters (optional)

```bash
cp filters.json.example filters.json
```

Edit `filters.json` to only get alerts for products you care about:

```json
{
  "alerts": [
    {
      "name": "Cheap MacBook Air",
      "category": "mac",
      "keywords": ["macbook air"],
      "max_price": 1000
    },
    {
      "name": "Any iPad Pro",
      "category": "ipad",
      "keywords": ["ipad pro"],
      "max_price": null
    }
  ]
}
```

**Filter options:**
- `name` — A label for your alert (for your reference)
- `category` — Restrict to a category: `mac`, `ipad`, `iphone`, `watch`, `airpods`, `appletv`, `homepod`
- `keywords` — All keywords must appear in the product title (case-insensitive)
- `max_price` — Maximum price threshold
- `min_price` — Minimum price threshold

If no `filters.json` exists, **all** new/returning products will trigger alerts.

### 4. Run the monitor

```bash
# Dry run — see what would be alerted without sending notifications:
python monitor.py --once --dry-run

# Single check (great for cron jobs):
python monitor.py --once

# Continuous monitoring (checks every N minutes):
python monitor.py

# Monitor specific categories only:
python monitor.py --categories mac,ipad
```

> **First run** indexes all current products. Alerts begin on the second run when changes are detected.

## Running with Cron

For a lightweight deployment, use cron instead of the built-in scheduler:

```bash
# Check every 15 minutes
*/15 * * * * cd /path/to/findthemac && /path/to/python monitor.py --once >> /var/log/findthemac.log 2>&1
```

## Running with Docker (optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "monitor.py"]
```

```bash
docker build -t findthemac .
docker run -d --env-file .env --name findthemac findthemac
```

## Project Structure

```
findthemac/
├── monitor.py              # Main entry point
├── src/
│   ├── scraper.py          # Apple refurbished page scraper
│   ├── tracker.py          # Product availability tracker (JSON DB)
│   ├── notifier.py         # Email & SMS notification sender
│   └── filters.py          # User-defined alert filters
├── data/
│   └── products.json       # Auto-generated product database (gitignored)
├── filters.json            # Your alert filters (create from example)
├── filters.json.example    # Example filter configuration
├── .env                    # Your credentials (gitignored)
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

## Supported Categories

| Category | URL |
|---|---|
| Mac | `/shop/refurbished/mac` |
| iPad | `/shop/refurbished/ipad` |
| iPhone | `/shop/refurbished/iphone` |
| Apple Watch | `/shop/refurbished/watch` |
| AirPods | `/shop/refurbished/airpods` |
| Apple TV | `/shop/refurbished/appletv` |
| HomePod | `/shop/refurbished/homepod` |

## Twilio Setup

1. Create a free account at [twilio.com](https://www.twilio.com/)
2. Get a phone number from the Twilio console
3. Copy your Account SID and Auth Token to `.env`
4. Verify the recipient phone number (required for trial accounts)

## License

MIT
