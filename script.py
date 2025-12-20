import os
import sys
import logging
from datetime import date
import tweepy
from dotenv import load_dotenv
from tweepy.errors import TweepyException
from google import genai

load_dotenv()

MAX_TWEET_LENGTH = 280


def _get_env_var(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return val


def paraphrase_for_tweet(text: str) -> str:
    """
    Uses Gemini to paraphrase raw learning text into a tweet.
    Always returns a string (empty string on failure).
    """
    if not text:
        return ""

    api_key = _get_env_var("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
Paraphrase the text below into a single tweet for learning in public.

Rules:
- Keep "Day X" or "Day <number>" exactly as written if present.
- Structure the tweet into 2–3 short lines for readability.
- Add a blank line between sections (use line breaks).
- Add 1–2 relevant emojis naturally.
- Tone should be clear, motivating, and slightly cool.
- Not too formal, not too casual.
- Use simple, easy-to-understand English.
- Avoid fancy or complex words.
- Include 1–3 relevant hashtags on the last line.
- Return ONLY one version.
- No explanations, no options, no formatting.
- STRICTLY limit the output to a maximum of 280 characters.

Text:
{text}
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt,
        )
    except Exception:
        logging.exception("Gemini API call failed")
        return ""

    tweet = response.text.strip()

    # Normalize excessive blank lines (max one empty line)
    while "\n\n\n" in tweet:
        tweet = tweet.replace("\n\n\n", "\n\n")

    # Hard safety net
    if len(tweet) > MAX_TWEET_LENGTH:
        tweet = tweet[: MAX_TWEET_LENGTH - 1] + "…"

    return tweet


def read_text_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_learning_update() -> str:
    """
    Reads raw learning text from text.txt and returns a paraphrased tweet.
    """
    try:
        raw_text = read_text_from_file("text.txt")
    except Exception as e:
        logging.error("Failed to read input text: %s", e)
        return ""

    if not raw_text:
        logging.error("text.txt is empty.")
        return ""

    logging.info("Paraphrasing learning update from text.txt")
    return paraphrase_for_tweet(raw_text)


def truncate_tweet(text: str) -> str:
    if not text:
        return ""

    if len(text) <= MAX_TWEET_LENGTH:
        return text

    logging.warning(
        "Tweet exceeded %s chars. Truncating automatically.", MAX_TWEET_LENGTH
    )
    return text[: MAX_TWEET_LENGTH - 1] + "…"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    # Initialize X client
    try:
        client = tweepy.Client(
            consumer_key=_get_env_var("X_API_KEY"),
            consumer_secret=_get_env_var("X_API_SECRET"),
            access_token=_get_env_var("X_ACCESS_TOKEN"),
            access_token_secret=_get_env_var("X_ACCESS_SECRET"),
        )
    except EnvironmentError as e:
        logging.error(e)
        return 2
    except Exception:
        logging.exception("Failed to initialize X client")
        return 3

    # Generate tweet
    tweet = generate_learning_update()
    tweet = truncate_tweet(tweet)

    if not tweet:
        logging.error("Generated tweet is empty.")
        return 4

    if dry_run:
        logging.info("DRY RUN ENABLED — Tweet not posted")
        print("\n--- TWEET PREVIEW ---\n")
        print(tweet)
        print("\n--------------------\n")
        return 0

    # Post tweet
    try:
        response = client.create_tweet(text=tweet)
    except TweepyException:
        logging.exception("X API error while posting tweet")
        return 5
    except Exception:
        logging.exception("Unexpected error while posting tweet")
        return 6

    tweet_id = response.data.get("id") if response and response.data else None

    logging.info("Tweet posted successfully")
    if tweet_id:
        logging.info("Tweet ID: %s", tweet_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
