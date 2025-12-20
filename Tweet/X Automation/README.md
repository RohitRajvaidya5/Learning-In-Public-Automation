# Learning in Public Tweet Automation 🚀

A Python automation tool that converts daily learning notes into clean, tweet-ready posts and publishes them on X (Twitter).   

The script reads raw learning text from a file, paraphrases it using Google Gemini with a learning-in-public tone, formats it for readability, enforces Twitter’s 280-character limit, and posts it automatically.

This project is built for consistent participation in challenges like **#100DaysOfCode**.

---

## Features

- Reads daily learning updates from a text file  
- Uses Google Gemini to paraphrase content into a tweet-friendly format  
- Preserves “Day X” progress tracking  
- Adds clean spacing, emojis, and relevant hashtags  
- Enforces Twitter’s 280-character limit  
- Supports dry-run mode for previewing tweets  
- Posts directly to X using Tweepy  

---

## Project Structure

```
.
├── script.py        # Main automation script
├── text.txt         # Raw learning input (editable daily)
├── .env             # Environment variables (not committed)
├── requirements.txt # Python dependencies
```

---

## Prerequisites

- Python 3.9+
- X (Twitter) Developer Account
- Google Gemini API key

---

## Installation

1. Clone the repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

2. Create and activate a virtual environment

```bash
python -m venv env
source env/bin/activate      # Linux / macOS
env\Scripts\activate       # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```
# Gemini
GEMINI_API_KEY=your_gemini_api_key

# X (Twitter)
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret

# Optional
DRY_RUN=true
```

> **Note:**  
> Keep `.env` in `.gitignore`. Never commit API keys.

---

## Usage

1. Write your daily learning update in `text.txt`

Example:

```
Day 18: Learned how Django serializers handle validation and why it matters in real APIs.
```

2. Run the script

```bash
python script.py
```

- If `DRY_RUN=true`, the tweet will be previewed in the console  
- If `DRY_RUN=false`, the tweet will be posted to X  

---

## Example Output

```
Day 18: Learned how Django serializers handle validation and why it matters in real APIs 💡

Small improvements today, fewer bugs tomorrow.

#100DaysOfCode #LearningInPublic
```

---

## Design Decisions

- **Single-purpose script**: Simple and easy to maintain  
- **File-based input**: Enables automation and scheduling  
- **Defensive coding**: Prevents crashes on empty input or API failures  
- **Hard character limit**: Ensures tweets are always valid  

---

## Future Improvements

- Auto-increment day count  
- Thread support for longer updates  
- Scheduled posting (cron / task scheduler)  
- Tweet history logging  
- CLI flags for interactive vs file-based input  

---

## Disclaimer

This project is intended for personal automation and learning-in-public workflows.  
Use responsibly and follow X platform policies.

---

## License

MIT License
