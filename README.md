# SubLife

SubLife is a Django + MySQL web application for tracking subscription usage, lifecycle state, waste, billing risk, and savings opportunities.

## What It Does

- Add subscriptions with category, monthly cost, billing day, and start date.
- Log daily subscription usage.
- Pause, resume, renew, or cancel a subscription.
- Calculate efficiency from used days in the current billing cycle.
- Calculate wasted rupees from billable unused days.
- Show lifecycle timeline bars for used, paused, and wasted days.
- Predict savings from a pause using the live simulator.
- Alert users when billing is within 3 days.
- Split total tracked spend by category.

## MySQL Setup

Create a database and user in MySQL:

```sql
CREATE DATABASE sublife_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sublife_user'@'localhost' IDENTIFIED BY 'sublife_password';
GRANT ALL PRIVILEGES ON sublife_db.* TO 'sublife_user'@'localhost';
FLUSH PRIVILEGES;
```

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:DJANGO_SECRET_KEY="change-me-for-production"
$env:DJANGO_DEBUG="True"
$env:DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
$env:MYSQL_DATABASE="sublife_db"
$env:MYSQL_USER="sublife_user"
$env:MYSQL_PASSWORD="sublife_password"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`, create an account, and start adding subscriptions.

The `.env.example` file is a reference for the environment variables. This project reads variables from the active shell environment.
