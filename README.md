# BioHelix

BioHelix is a plain-language reference for biology, chemistry, and biotechnology basics. It covers 18 topics organized by subject, each with a short explanation and links to outside resources. A search box helps you find topics fast, with an AI fallback for anything not listed. Interactive exercises for each topic are planned but not yet built.

## Setup & Running

### Prerequisites
- Python 3.7 or higher
- An Anthropic API key (for the Lab AI feature)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key:**
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to `.env`:
     ```
     ANTHROPIC_API_KEY=your_actual_key_here
     PORT=3000
     ```

### Running Locally

```bash
python3 server.py
```

Then open http://localhost:3000 in your browser.

### Deployment Notes

- The API key is stored server-side in `.env` and never exposed to the frontend
- The `/api/ask` endpoint securely proxies requests to Anthropic's API
- Update the `PORT` environment variable if needed

