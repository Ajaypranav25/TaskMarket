# TaskMarket — AI-Evaluated Task Marketplace

A full-stack Django platform where companies post tasks, workers complete them, and AI instantly evaluates every submission — scoring quality and paying workers accordingly.

---

## ✨ Features

| Feature | Description |
|---|---|
| **AI Evaluation** | Every submission is scored 0-100 by Claude AI with detailed feedback |
| **Level Progression** | Workers advance through 5 levels (Rookie → Master) based on avg score |
| **Dynamic Earnings** | Pay = reward × (score/100) × level multiplier |
| **Company Tools** | Post tasks, set level requirements, review all submissions |
| **Leaderboard** | Real-time ranking of top workers by average AI score |
| **Rich Dashboard** | Role-aware dashboards for workers and companies |

## 🏗️ Tech Stack

- **Backend**: Django 4.2, SQLite
- **AI**: Anthropic Claude (claude-sonnet-4-20250514)
- **Frontend**: Vanilla HTML/CSS/JS — dark editorial aesthetic
- **Fonts**: Syne + Space Mono + DM Sans (Google Fonts)
- **Static Files**: WhiteNoise

---

## 🚀 Quick Setup

### 1. Clone / unzip the project
```bash
cd taskmarket
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Windows PowerShell:
# $env:ANTHROPIC_API_KEY = "sk-ant-..."
```

### 5. Run migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 6. Seed demo data (optional)
```bash
python manage.py seed_demo
```

### 7. Create admin user
```bash
python manage.py createsuperuser
```

### 8. Start the server
```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000)

---

## 👤 Demo Accounts (after seed_demo)

| Role | Username | Password |
|---|---|---|
| Company | `acmecorp` | `demo1234` |
| Worker (Level 3) | `alice_dev` | `demo1234` |
| Worker (Level 4) | `carol_pro` | `demo1234` |
| Worker (Level 2) | `bob_writer` | `demo1234` |

---

## 🗂️ Project Structure

```
taskmarket/
├── manage.py
├── requirements.txt
├── taskmarket/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                    # Main application
│   ├── models.py            # Level, UserProfile, Task, Submission
│   ├── views.py             # All views
│   ├── urls.py              # URL routing
│   ├── admin.py             # Admin config
│   ├── ai_evaluator.py      # Claude AI integration
│   ├── apps.py
│   ├── migrations/
│   │   ├── 0001_initial.py  (auto-generated)
│   │   └── 0002_initial_levels.py
│   └── management/
│       └── commands/
│           └── seed_demo.py
├── templates/
│   └── core/
│       ├── base.html
│       ├── index.html           # Landing page
│       ├── login.html
│       ├── register.html
│       ├── worker_dashboard.html
│       ├── company_dashboard.html
│       ├── task_list.html
│       ├── task_detail.html
│       ├── submission_detail.html
│       ├── my_submissions.html
│       ├── task_submissions.html
│       ├── post_task.html
│       ├── profile.html
│       └── leaderboard.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

---

## 📐 Level System

| Level | Name | Avg Score Req | Min Submissions | Reward Multiplier |
|---|---|---|---|---|
| 1 | Rookie | 0 | 0 | 1.0× |
| 2 | Contributor | 60 | 3 | 1.1× |
| 3 | Specialist | 70 | 10 | 1.25× |
| 4 | Expert | 80 | 25 | 1.5× |
| 5 | Master | 90 | 50 | 2.0× |

## 💰 Earnings Formula

```
earnings = task_reward × (ai_score / 100) × level_multiplier
```

Example: $50 task, score 85, Level 3 (1.25×) → **$53.13**

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required for AI evaluation) |
| `SECRET_KEY` | Django secret key (change for production) |
| `DEBUG` | Set to `False` in production |

---

## 🛠️ Admin Panel

Visit `/admin/` after creating a superuser. Manage levels, tasks, users, and view all submissions.

---

## 🚢 Production Notes

1. Set `DEBUG = False` in `settings.py`
2. Set a strong `SECRET_KEY`
3. Configure a production database (PostgreSQL recommended)
4. Set `ALLOWED_HOSTS` properly
5. Run `python manage.py collectstatic`
6. Use gunicorn + nginx
