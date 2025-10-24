language_app_backend/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── otp.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── auth.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── jwt_tokens.py
│   │   ├── emailer.py
│   └── __init__.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── requirements.txt
└── .env
