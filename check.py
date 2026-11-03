
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

response = session.get(
    "https://r.jina.ai/" + URL,
    timeout=(15, 120),
    headers={"X-Respond-With": "markdown"}
)

response.raise_for_status()
content = response.text

# Extract movie titles using their metadata
lines = content.splitlines()
movies = {}

for i, line in enumerate(lines):
    heading = re.match(r"^#{2,6}\s+(.+?)\s*$", line)

    if not heading:
        continue

    name = heading.group(1).strip()

    # Look for the movie information immediately below
    next_line = ""
    for following in lines[i + 1:]:
        if following.strip():
            next_line = following.strip()
            break

    if re.search(
        r"^(G|PG|PG-13|R|12\+|16\+|18\+|18TC)\s+.*\d+\s*min\b",
        next_line,
        re.IGNORECASE
    ):
        movies[name] = name

print("Found", len(movies), "movies")

if not movies:
    print("Could not identify movie titles.")
    print("Website response preview:")
    print(content[:3000])
    sys.exit("Movie extraction failed")

# Load previously seen movies
seen = set(json.load(open(FILE))) if os.path.exists(FILE) else None

# Notify only about newly appearing movies
if seen is not None:
    for name in sorted(set(movies) - seen):
        result = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
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
    json.dump(
        sorted((seen or set()) | set(movies)),
        f,
        ensure_ascii=False
    )

print("Movie database updated successfully")
