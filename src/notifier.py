"""Notification system for sending email and SMS alerts.

Supports:
- Email via SMTP (works with Gmail, Outlook, or any SMTP provider)
- SMS via Twilio API
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _build_product_html(products: list[dict], section_title: str) -> str:
    """Build an HTML section listing products."""
    if not products:
        return ""

    rows = ""
    for p in products:
        rows += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #eee;">
                <a href="{p['url']}" style="color:#0066cc; text-decoration:none; font-weight:bold;">
                    {p['title']}
                </a>
            </td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; white-space:nowrap;">
                <strong>${p['price']}</strong>
                <br><span style="color:#888; text-decoration:line-through; font-size:0.9em;">${p['original_price']}</span>
                <br><span style="color:#2e8b57; font-size:0.9em;">{p['savings']}</span>
            </td>
        </tr>
        """

    return f"""
    <h2 style="color:#333; border-bottom:2px solid #0066cc; padding-bottom:8px;">{section_title}</h2>
    <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
        {rows}
    </table>
    """


def _build_product_text(products: list[dict], section_title: str) -> str:
    """Build a plain-text section listing products."""
    if not products:
        return ""

    lines = [f"\n{'=' * 40}", section_title, "=" * 40]
    for p in products:
        lines.append(f"\n  {p['title']}")
        lines.append(f"  Price: ${p['price']} (was ${p['original_price']}) — {p['savings']}")
        lines.append(f"  {p['url']}")
    return "\n".join(lines)


def build_alert_email(new_products: list[dict], back_in_stock: list[dict]) -> tuple[str, str, str]:
    """Build the email subject, HTML body, and plain-text body.

    Returns:
        Tuple of (subject, html_body, text_body).
    """
    total = len(new_products) + len(back_in_stock)
    subject = f"Apple Refurbished Alert: {total} product(s) now available!"

    html_parts = [
        '<div style="font-family:Arial,sans-serif; max-width:600px; margin:0 auto;">',
        '<h1 style="color:#333;">Apple Refurbished Store Alert</h1>',
        f'<p style="color:#555;">We found <strong>{total}</strong> product(s) that are now available.</p>',
    ]
    text_parts = [
        "Apple Refurbished Store Alert",
        f"We found {total} product(s) that are now available.\n",
    ]

    if back_in_stock:
        html_parts.append(_build_product_html(back_in_stock, "Back In Stock"))
        text_parts.append(_build_product_text(back_in_stock, "BACK IN STOCK"))

    if new_products:
        html_parts.append(_build_product_html(new_products, "New Listings"))
        text_parts.append(_build_product_text(new_products, "NEW LISTINGS"))

    html_parts.append(
        '<p style="color:#999; font-size:0.8em; margin-top:20px;">'
        'Sent by FindTheMac — Apple Refurbished Product Monitor</p></div>'
    )

    return subject, "\n".join(html_parts), "\n".join(text_parts)


def build_sms_body(new_products: list[dict], back_in_stock: list[dict]) -> str:
    """Build a concise SMS message body.

    SMS has character limits, so we keep it brief and link to the store.
    """
    lines = ["Apple Refurb Alert!\n"]

    all_products = back_in_stock + new_products
    # Show up to 3 products in SMS to keep it short
    for p in all_products[:3]:
        lines.append(f"- {p['title'][:60]}... ${p['price']}")

    if len(all_products) > 3:
        lines.append(f"\n+{len(all_products) - 3} more")

    lines.append("\nhttps://www.apple.com/shop/refurbished")
    return "\n".join(lines)


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """Send an email notification via SMTP.

    Returns:
        True if sent successfully, False otherwise.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        logger.info("Email sent to %s", to_addr)
        return True
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False


def send_sms(
    account_sid: str,
    auth_token: str,
    from_number: str,
    to_number: str,
    body: str,
) -> bool:
    """Send an SMS notification via Twilio.

    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number,
        )
        logger.info("SMS sent to %s (SID: %s)", to_number, message.sid)
        return True
    except ImportError:
        logger.error("Twilio library not installed. Run: pip install twilio")
        return False
    except Exception as exc:
        logger.error("Failed to send SMS: %s", exc)
        return False
