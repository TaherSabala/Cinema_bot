
import requests, json, os, sys, re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://egy.voxcinemas.com/showtimes/city-centre-almaza"
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

# Connect through Jina Reader
session = requests.Session()

retry = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504]
)

session.mount("https://", HTTPAdapter(max_retries=retry))

reader_url = "https://r.jina.ai/" + URL

response = session.get(
    reader_url,
    timeout=(15, 120),
    headers={
        "X-Respond-With": "markdown",
        "X-Timeout": "90"
    }
)

response.raise_for_status()

content = response.text

# Extract movie titles from page headings
movies = {}

for line in content.splitlines():
    match = re.match(r"^##\s+(.+?)\s*$", line)

    if match:
        name = match.group(1).strip()

        if name not in ["View Times and Book", "Image"]:
            name = re.sub(r"\*\*", "", name)
            movies[name] = name

print("Found", len(movies), "movies")

if not movies:
    sys.exit("No movies found. Check the website response.")

# Load previously seen movies
seen = set(json.load(open(FILE))) if os.path.exists(FILE) else None

# Notify only about newly appearing movies
if seen is not None:
    for name in sorted(set(movies) - seen):
        telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        result = requests.get(
            telegram_url,
            params={
                "chat_id": CHAT_ID,
                "text": f"New movie at VOX City Centre Almaza: {name}\n{URL}"
            },
            timeout=30
        )

        result.raise_for_status()

        if not result.json().get("ok"):
            sys.exit("Telegram notification failed")

        print("Notified:", name)

# Save current movie list
with open(FILE, "w") as f:
    json.dump(sorted((seen or set()) | set(movies)), f, ensure_ascii=False)

print("Movie database updated successfully")
