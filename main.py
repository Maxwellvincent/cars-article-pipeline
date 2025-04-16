import feedparser
import requests
from newspaper import Article
import json
import os 

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Define RSS Feed
# rss_url = "https://www.nybooks.com/feed/"
rss_url = "https://www.theatlantic.com/feed/all/"
response = requests.get(rss_url, headers=headers)

feed = feedparser.parse(response.text)
print(f"Found {len(feed.entries)} articles in RSS feed")

# keyword Categories
keywords = {
    "contrast": ['however', 'but', 'although', 'yet', 'nevertheless', 'rather', 'in contrast', 'on the other hand', 'otherwise', 'nevertheless', 'wheras', 'while', 'different', 'unlike'],
    "similarity": ['and', 'also', 'moreover', 'futhermore', 'like', 'same', 'similar','that is', 'in other words', 'for example', 'for instance', 'take the case of', 'including', 'such as', 'in addition', 'at the same time', 'as well as', 'equally', 'this','that', 'these', 'those', ';',':', '-'],
    "opposition": ['not', 'never', 'none', 'on the contrary', 'as opposed to', 'versus', 'otherwise'],
    "emphasis": ['indeed', 'in fact', 'clearly', 'must', 'above all'],
    "moderating": ['can', 'could', 'may', 'might', 'possibly', 'probably', 'sometimes', 'on occasion', 'often', 'tends to', 'here', 'now', 'in this case', 'in some sense'],
    "logic": ['because', 'since', 'therefore', 'as a result', 'due to']
}

#output list

article_data = []

# Fetch and process first 3 articles
for entry in feed.entries[:3]:
    print(f"Processing: {entry.title}")
    try:
        article = Article(entry.link)
        article.download()
        article.parse()
        print("✅ Article downloaded and parsed")
    except Exception as e:
        print(f"Skipping {entry.title} due to error: {e}")
        continue
    
    paragraphs = [p.strip() for p in article.text.split('\n') if len(p.strip()) > 80]
    processed_paragraphs = []
    
    for para in paragraphs:
        tags = []
        for tag, words in keywords.items():
            if any(word in para.lower() for word in words):
                tags.append(tag)
        processed_paragraphs.append({
            "text": para,
            "tags": tags
        })
        
        article_data.append({
            "title": entry.title,
            "url": entry.link,
            "paragraphs": processed_paragraphs
        })
        
# Save to JSON
os.makedirs("data", exist_ok=True)
with open("data/articles.json", "w", encoding="utf-8") as f:
    json.dump(article_data, f, indent=2)
    
print("✅ Saved data to data/articles.json")