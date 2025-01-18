# URL Shortener

A Django-based URL shortener with expiry and analytics features with optional password protection.

## Features

- Shorten long URLs to unique short codes
- Set custom expiration times (defaults to 24 hours)
- Optional password protection for URLs
- Track access analytics (timestamps and IP addresses)
- Idempotent URL shortening (same long URL generates same short code)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Create Shortened URL 