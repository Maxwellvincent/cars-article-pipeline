import requests
import feedparser

headers = {
    "User-Agent": "Mozilla/5.0"
}
rss_url = "https://www.theatlantic.com/feed/all/"

# Try getting the raw feed content
response = requests.get(rss_url, headers=headers)
print("Status Code:", response.status_code)
print("First 500 chars:\n", response.text[:500])

# Try parsing it
feed = feedparser.parse(response.text)
print("Parsed articles:", len(feed.entries))
