import requests

url = 'https://api.marketaux.com/v1/news/all?countries=us&filter_entities=true&limit=3&published_after=2025-08-06T13:08&api_token='

response = requests.get(url)
data = response.json()

if response.status_code == 200:
    print("Got the data")

results = []

for article in data.get("data",[]):
    results.append({
        "uuid": article.get("uuid"),
        "title": article.get("title"),
        "description": article.get("description")
    })

    for similar_article in article.get("similar", []):
        results.append({
            "uuid": similar_article.get("uuid"),
            "title": similar_article.get("title"),
            "description": similar_article.get("description")
        })


for item in results:
    print(f"UUID: {item['uuid']}")
    print(f"Title: {item['title']}")
    print(f"Description: {item['description']}")
    print("=" * 60)
