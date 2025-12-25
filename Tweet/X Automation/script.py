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
MAX_LINKEDIN_LENGTH = 3000
LINKEDIN_SEE_MORE_LIMIT = 200


def _get_env_var(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return val


def paraphrase_for_tweet(text: str) -> str:
    """
    Uses Gemini to paraphrase raw learning text into a tweet.
    """
    if not text:
        return ""

    api_key = _get_env_var("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
Paraphrase the text below into a single tweet for learning in public.

Rules:
- Keep "Day X" or "Day <number>" exactly as written if present.
- Structure the tweet into 2–3 short lines.
- Add a blank line between sections.
- Add 1–2 relevant emojis.
- Tone should be clear, motivating, and slightly cool.
- Simple English only.
- Include 1–3 hashtags on the last line.
- STRICT limit: 280 characters.
- Return ONLY the tweet.

Text:
{text}
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt,
        )
    except Exception:
        logging.exception("Gemini API call failed for Twitter")
        return ""

    tweet = response.text.strip()

    while "\n\n\n" in tweet:
        tweet = tweet.replace("\n\n\n", "\n\n")

    if len(tweet) > MAX_TWEET_LENGTH:
        tweet = tweet[: MAX_TWEET_LENGTH - 1] + "…"

    return tweet


def paraphrase_for_linkedin(text: str) -> str:
    """
    Uses Gemini to generate a LinkedIn learning-in-public post.
    """
    if not text:
        return ""

    api_key = _get_env_var("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
Rewrite the text below as a LinkedIn learning-in-public post.

Rules:
- First ~200 characters must hook the reader before "See more".
- Use short paragraphs and spacing.
- Bold important points using **bold**.
- Professional, authentic tone.
- Simple English.
- 0–2 emojis max.
- Add 3–5 relevant hashtags at the end.
- Max length: 3000 characters.
- Return ONLY the post content.

Text:
{text}
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt,
        )
    except Exception:
        logging.exception("Gemini API call failed for LinkedIn")
        return ""

    post = response.text.strip()

    if len(post) > MAX_LINKEDIN_LENGTH:
        post = post[: MAX_LINKEDIN_LENGTH - 1] + "…"

    return post


def read_text_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_learning_update() -> tuple[str, str]:
    """
    Reads raw learning text and returns:
    (tweet, linkedin_post)
    """
    try:
        raw_text = read_text_from_file("input.txt")
    except Exception as e:
        logging.error("Failed to read input text: %s", e)
        return "", ""

    if not raw_text:
        logging.error("input.txt is empty.")
        return "", ""

    logging.info("Generating learning updates")

    tweet = paraphrase_for_tweet(raw_text)
    linkedin_post = paraphrase_for_linkedin(raw_text)

    return tweet, linkedin_post


def truncate_tweet(text: str) -> str:
    if not text:
        return ""

    if len(text) <= MAX_TWEET_LENGTH:
        return text

    return text[: MAX_TWEET_LENGTH - 1] + "…"


def save_output(tweet: str, linkedin_post: str, path: str = "output.txt", note: str | None = None) -> None:
    """Save the generated tweet and LinkedIn post into `output.txt` with timestamp and optional note."""
    from datetime import datetime

    header = f"===== Generated on {datetime.utcnow().isoformat()}Z =====\n"
    contents = [header]
    if note:
        contents.append(f"NOTE: {note}\n")
    contents.append("--- X / TWEET ---\n")
    contents.append(tweet.rstrip() + "\n\n")
    contents.append("--- LINKEDIN POST ---\n")
    contents.append(linkedin_post.rstrip() + "\n")
    contents.append("\n")

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.writelines(contents)
        logging.info("Saved outputs to %s", path)
    except Exception:
        logging.exception("Failed to write outputs to %s", path)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    import argparse

    parser = argparse.ArgumentParser(description="Generate and post learning-in-public updates to X and save outputs")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm posting (non-interactive)")
    parser.add_argument("--output", "-o", default="output.txt", help="Path to save generated outputs")
    args = parser.parse_args()

    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    tweet, linkedin_post = generate_learning_update()
    tweet = truncate_tweet(tweet)

    if not tweet:
        logging.error("Generated tweet is empty.")
        return 4

    if not linkedin_post:
        logging.error("Generated LinkedIn post is empty.")
        return 5

    # Always save outputs locally
    save_output(tweet, linkedin_post, path=args.output, note=("DRY RUN" if dry_run else None))

    # Show previews
    print("\n--- X / TWITTER PREVIEW ---\n")
    print(tweet)

    print("\n--- LINKEDIN POST PREVIEW ---\n")
    print(linkedin_post)

    # If dry run, do not post anything
    if dry_run:
        logging.info("DRY RUN ENABLED — No posts published")
        return 0

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

    # Confirm before posting
    confirmed = args.yes
    if not confirmed:
        try:
            resp = input("Post the tweet now? (y/N): ").strip().lower()
        except Exception:
            logging.warning("No TTY available; refusing to post without --yes flag")
            resp = "n"
        confirmed = resp == "y"

    if not confirmed:
        logging.info("Posting skipped by user")
        save_output(tweet, linkedin_post, path=args.output, note="User skipped posting")
        return 0

    # Post tweet
    try:
        response = client.create_tweet(text=tweet)
    except TweepyException:
        logging.exception("X API error while posting tweet")
        save_output(tweet, linkedin_post, path=args.output, note="Failed to post tweet (API error)")
        return 6
    except Exception:
        logging.exception("Unexpected error while posting tweet")
        save_output(tweet, linkedin_post, path=args.output, note="Failed to post tweet (unexpected error)")
        return 7

    tweet_id = response.data.get("id") if response and response.data else None

    logging.info("Tweet posted successfully")
    if tweet_id:
        logging.info("Tweet ID: %s", tweet_id)
        save_output(tweet, linkedin_post, path=args.output, note=f"Tweet posted (id={tweet_id})")
    else:
        save_output(tweet, linkedin_post, path=args.output, note="Tweet posted (no id returned)")

    # LinkedIn is intentionally NOT auto-posted
    logging.info("LinkedIn post generated (manual posting recommended)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
