# Flask Authentication App

A basic Flask application with user authentication using Flask-Login and SQLite database with SQLAlchemy.

## Features

- User registration and login
- SQLite database with SQLAlchemy ORM
- Bootstrap 5 responsive design
- Flash messages for user feedback
- Secure password hashing
- User session management

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. Initialize the database:
   ```
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```
6. Run the application:
   ```
   flask run
   ```
7. Open http://localhost:5000 in your browser

## Project Structure

```
.
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── instance/             # Instance folder (created automatically)
│   └── app.db          # SQLite database (created after first run)
└── templates/            # HTML templates
    ├── base.html        # Base template
    └── index.html       # Home page
```

## License

MIT
