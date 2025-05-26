# ProfitFlow: AI-Powered Financial Tracker for Small Traders

## 🚀 Project Overview

ProfitFlow is a lightweight, intuitive, and intelligent web application designed to empower micro and small business owners to effortlessly track their income and expenses in real-time. By leveraging cutting-edge **Google Gemini AI**, ProfitFlow allows users to record financial transactions simply by speaking or taking a photo of a receipt, providing instant clarity on their business's profitability.

No more pen-and-paper ledgers or complex spreadsheets! ProfitFlow makes financial management accessible, accurate, and actionable for the everyday trader.

## 🔗 Important Links

* **Live Prototype:** [ProfitFlow](https://profitflow.unicodeonesolutions.com/)
* **Pitch Deck (Canva):** [ProfitFlow Pitch Deck](https://www.canva.com/design/DAGogacxMd0/yoUY9FwSudQU6cSmZW6JOA/view?utm_content=DAGogacxMd0&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h2d57e03dfa)
* **Google AI Studio:** [https://aistudio.google.com/](https://aistudio.google.com/) (For obtaining your Gemini API Key)


## ✨ Key Features

* **🎙️ AI-Powered Voice Input:** Speak your transaction details (e.g., "Sold 100 dollars of vegetables," "Paid 200 for rent"), and Gemini AI intelligently transcribes and extracts the relevant financial data.
* **📸 AI-Powered Photo (OCR) Input:** Snap a picture of any receipt or invoice, and Gemini AI extracts key information like amount, date, description, and merchant.
* **📊 Real-time Profit & Loss:** Get an immediate overview of your income, expenses, and net profit through a clear, intuitive dashboard.
* **🏷️ Smart Categorization:** AI-driven categorization helps organize transactions automatically, making financial reporting a breeze.
* **👤 Secure User Authentication:** Robust user registration, login, and session management using Flask-Login and secure password hashing.
* **📱 Responsive & Engaging UI/UX:** Built with a modern, responsive design (using Bootstrap 5) ensuring a seamless experience across devices. Includes subtle animations and sound feedback for enhanced interactivity.
* **🗄️ Reliable Data Storage:** Utilizes a lightweight SQLite database with SQLAlchemy ORM for efficient and secure data management.
* **⚡ Flash Messages:** Instant user feedback for actions like successful logins or form submissions.

## 🌟 Why ProfitFlow? (Addressing the Problem)

Many small traders operate without proper financial records, making it impossible to know if they're truly profitable, hindering growth, and limiting access to critical financial services. ProfitFlow solves this by democratizing financial tracking, turning a tedious task into a quick, voice or photo-driven interaction.

## 🛠️ Setup and Installation

Follow these steps to get ProfitFlow running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/profitflow.git](https://github.com/your-username/profitflow.git)
    cd profitflow
    ```
    (Replace `your-username/profitflow.git` with your actual repository URL)

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: This includes `google-generativeai` for Gemini API interaction.)*

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your `GEMINI_API_KEY` and a Flask `SECRET_KEY`.
    ```bash
    cp .env.example .env
    # Open .env and add your actual API key and a strong secret key
    # Example .env content:
    # GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    # SECRET_KEY="YOUR_VERY_STRONG_FLASK_SECRET_KEY"
    ```
    *You can get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).*

5.  **Initialize the database:**
    ```bash
    flask shell
    >>> from app import db
    >>> db.create_all()
    >>> exit()
    ```
    *This will create the `instance/app.db` SQLite database file.*

6.  **Run the application:**
    ```bash
    flask run
    ```

7.  **Access the application:**
    Open your web browser and navigate to `http://localhost:5000`.

## 📂 Project Structure

```
├── app.py                  # Main Flask application file (routes, logic, Gemini integration)
├── config.py               # Application configuration settings (debug mode, secret key)
├── requirements.txt        # List of Python dependencies
├── secrets.env             # Example environment variables file
├── secrets.env             # Your local environment variables (gitignore'd)
├── instance/               # Flask instance folder (for app-specific data)
│   └── app.db              # SQLite database file
├── static/                 # Static assets (CSS, JS, images, sound effects)
│   ├── css/
│   ├── js/
│   └── audio/
└── templates/              # HTML templates for all pages
    ├── base.html           # Base layout template
    ├── index.html          # Home page
    ├── register.html       # User registration form
    ├── login.html          # User login form
    ├── create_receipt.html # Form for adding new transactions
    ├── view_receipts.html  # Display list of user's transactions
    └── dashboard.html      # User dashboard
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.