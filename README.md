# FindTheMac — Apple Refurbished Product Alert System

A single-page web application that lets you browse every Apple product from the last 5 years, check if it's currently available on [Apple's Refurbished Store](https://www.apple.com/shop/refurbished), and set up **email** and **SMS text message** alerts for when it becomes available.

## How It Works

1. **Browse** — The app displays a visual catalog of all Apple products (Mac, iPad, iPhone, Watch, AirPods, Apple TV, HomePod) released from 2021 to 2025.
2. **Select** — Click any product to see if it's currently listed on Apple Refurbished.
3. **Subscribe** — Enter your email and/or phone number to set up an alert.
4. **Get Notified** — If the product is available now, you're notified immediately. If not, the background monitor checks every 15 minutes and notifies you the moment it appears.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your SMTP and Twilio credentials:

| Variable | Description |
|---|---|
| `SMTP_HOST` | SMTP server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USERNAME` | Your email login |
| `SMTP_PASSWORD` | App-specific password |
| `EMAIL_FROM` | Sender address |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Your Twilio phone number |
| `CHECK_INTERVAL_MINUTES` | Monitor frequency (default: `15`) |

> **Gmail users:** Use an [App Password](https://support.google.com/accounts/answer/185833) — regular passwords won't work with 2FA.

### 3. Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Architecture

```
findthemac/
├── app.py                  # Flask web server + API + background monitor
├── products.py             # Apple product catalog (2021–2025)
├── templates/
│   └── index.html          # Single-page frontend (HTML/CSS/JS)
├── data/
│   └── findthemac.db       # SQLite database (auto-created, gitignored)
├── .env                    # Your credentials (gitignored)
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

### Backend (`app.py`)

- **Flask** web server serving the SPA and JSON API
- **SQLite** database for alert subscriptions and refurbished product cache
- **Background thread** that scrapes Apple's refurbished store every N minutes
- **Keyword matching** engine that maps catalog products to refurbished listings
- **SMTP email** sender with rich HTML templates
- **Twilio SMS** sender for text message alerts

### Frontend (`templates/index.html`)

- Self-contained SPA — no build tools, no npm, no frameworks
- Visual product grid with images for all Apple products
- Category tabs (Mac, iPad, iPhone, Watch, AirPods, Apple TV, HomePod)
- Real-time search across product names and specs
- Modal with live refurbished availability check
- Alert signup form with email and/or SMS options

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products` | Full product catalog |
| GET | `/api/refurbished/status/<id>` | Check refurbished availability for a product |
| GET | `/api/refurbished/summary` | Count of available refurbished products by category |
| POST | `/api/alerts` | Create a new alert subscription |
| GET | `/api/alerts/check` | Get active alert count |

## Twilio Setup (for SMS)

1. Create a free account at [twilio.com](https://www.twilio.com/)
2. Get a phone number from the Twilio console
3. Copy Account SID and Auth Token to `.env`
4. Verify recipient phone numbers (required on trial accounts)

## Docker (optional)

```bash
docker build -t findthemac .
docker run -d -p 5000:5000 --env-file .env findthemac
```

## License

MIT
