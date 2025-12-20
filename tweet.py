import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def paraphrase_text(text: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Paraphrase the text below into a single tweet for learning in public.

Rules:
- Keep "Day X" or "Day <number>" exactly as written if present.
- Add 1–2 relevant emojis naturally (not excessive).
- Tone should be clear, motivating, and slightly cool.
- Not too formal, not too casual.
- Use simple, easy-to-understand English.
- Avoid fancy or complex words.
- Include 1–3 relevant hashtags at the end (like #100DaysOfCode, #LearningInPublic, #BuildInPublic, #Coding).
- Use only hashtags that fit the content.
- Return ONLY one version.
- No explanations, no options, no formatting.
- STRICTLY limit the output to a maximum of 280 characters.

Text:
{text}

"""

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt,
    )

    tweet = response.text.strip().replace("\n", " ")

    # Hard safety for Twitter
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return tweet


def read_input_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


if __name__ == "__main__":
    try:
        user_input = read_input_from_file("input.txt")

        if not user_input:
            print("input.txt is empty.")
        else:
            print("\nParaphrased Output:\n")
            print(paraphrase_text(user_input))

    except Exception as e:
        print(f"Error: {e}")
