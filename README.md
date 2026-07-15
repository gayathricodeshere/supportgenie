# 🧞 SupportGenie — Nimbus Support Chatbot

SupportGenie is an AI-powered customer support chatbot built with **Streamlit**, **Groq (Llama 3.3 70B)**, and **ChromaDB**. It handles order lookups, refund requests, policy questions (via RAG), and escalations to a human agent — all through a simple chat interface.

## Features

- **Intent classification** — routes each message to the right handler (policy question, order lookup, refund request, escalation, or off-topic) using an LLM-based router.
- **Retrieval-Augmented Generation (RAG)** — answers policy questions (shipping, returns, warranty, refunds) using a ChromaDB vector store built from a small knowledge base, with citations.
- **Order lookup** — checks order status, ETA, and total from a mock orders database.
- **Refund flow** — confirms with the user before processing a refund ("yes/no" guardrail).
- **Escalation** — creates a support ticket for issues the bot can't resolve.

## Tech Stack

- [Streamlit](https://streamlit.io/) — chat UI
- [Groq](https://groq.com/) — LLM inference (`llama-3.3-70b-versatile`)
- [ChromaDB](https://www.trychroma.com/) — vector store for policy Q&A
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/supportgenie.git
cd supportgenie
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 5. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage

Try asking:
- `"Where is order NIM-4821?"`
- `"What's your return policy?"`
- `"I want a refund for NIM-3310"`
- `"I need to talk to a human"`

## Project Structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .env                 # API keys (not committed)
├── .gitignore
└── README.md
```

## Notes

- Order data and the help-docs knowledge base are currently hardcoded/mocked for demo purposes.
- `.env` and `venv/` are excluded from version control via `.gitignore` — never commit your API key.

## License

MIT
