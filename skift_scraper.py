import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime, timedelta
import time

DB_PATH = "skift_articles.db"
NEWS_URL = "https://skift.com/news/"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            publication_timestamp TEXT,
            source TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

def parse_timestamp(text):
    # Example: "Yesterday at 10:10 PM GMT+5:30" or "Today at 12:36 AM GMT+5:30"
    if not text:
        return None
    today_match = re.match(r"Today at (.+) GMT", text)
    yesterday_match = re.match(r"Yesterday at (.+) GMT", text)
    if today_match:
        time_part = today_match.group(1).strip()
        dt = datetime.now().strftime("%Y-%m-%d")
        full_str = f"{dt} {time_part}"
        try:
            return datetime.strptime(full_str, "%Y-%m-%d %I:%M %p")
        except Exception:
            return None
    if yesterday_match:
        time_part = yesterday_match.group(1).strip()
        dt = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        full_str = f"{dt} {time_part}"
        try:
            return datetime.strptime(full_str, "%Y-%m-%d %I:%M %p")
        except Exception:
            return None
    # Try ISO format fallback
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None

def fetch_article_details(url):
    """Fetch the article page and extract content and timestamp."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch article {url}: {e}")
        return {"content": "", "publication_timestamp": ""}

    soup = BeautifulSoup(resp.text, "html.parser")
    # Extract main article content
    content = ""
    main_section = soup.find("section", class_=re.compile(r"t-single-news__content"))
    if main_section:
        # Join all <p> tags' text
        paragraphs = main_section.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    # Try to extract "Skift Take" if present
    skift_take = soup.find("section", class_=re.compile(r"c-skift-take"))
    if skift_take:
        skift_take_p = skift_take.find("p")
        if skift_take_p:
            content = skift_take_p.get_text(strip=True) + "\n" + content

    # Extract timestamp from byline
    pub_ts = ""
    byline_time = soup.find("div", class_="c-byline__date")
    if byline_time:
        time_tag = byline_time.find("time")
        if time_tag:
            # Prefer datetime attribute if present
            if time_tag.has_attr("datetime"):
                pub_ts = time_tag["datetime"]
            else:
                # Try to parse the visible string
                pub_ts = time_tag.get_text(strip=True)
                dt = parse_timestamp(pub_ts)
                if dt:
                    pub_ts = dt.isoformat()
    return {"content": content, "publication_timestamp": pub_ts}

def fetch_articles():
    try:
        resp = requests.get(NEWS_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Network error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    seen_urls = set()

    # Find all article blocks by class
    for article in soup.find_all("article", class_="c-tease"):
        try:
            h3 = article.find("h3", class_="c-tease__title")
            if not h3:
                continue
            a_tag = h3.find("a", href=True)
            if not a_tag:
                continue
            url = a_tag["href"]
            title = a_tag.get_text(strip=True)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Get the publication timestamp from <time> tag if present
            pub_ts = ""
            time_tag = article.find("time")
            if time_tag and time_tag.has_attr("datetime"):
                pub_ts = time_tag["datetime"]

            # Fetch article details (content and possibly better timestamp)
            details = fetch_article_details(url)
            content = details["content"]
            # Prefer timestamp from article page if available
            if details["publication_timestamp"]:
                pub_ts = details["publication_timestamp"]

            articles.append({
                "url": url,
                "title": title,
                "publication_timestamp": pub_ts,
                "source": "skift.com",
                "content": content
            })
        except Exception as e:
            print(f"Error parsing article: {e}")
    return articles

def save_articles(articles):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    new_count = 0
    for art in articles:
        try:
            c.execute("""
                INSERT INTO articles (url, title, publication_timestamp, source, content)
                VALUES (?, ?, ?, ?, ?)
            """, (art["url"], art["title"], art["publication_timestamp"], art["source"], art["content"]))
            new_count += 1
        except sqlite3.IntegrityError:
            continue
        except Exception as e:
            print(f"DB error: {e}")
    conn.commit()
    conn.close()
    print(f"Added {new_count} new articles.")

def show_recent_articles():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT title, url, publication_timestamp, content FROM articles
        ORDER BY publication_timestamp DESC
        LIMIT 5
    """)
    rows = c.fetchall()
    conn.close()
    print("\n5 Most Recent Articles:")
    for row in rows:
        snippet = (row[3][:200] + "...") if row[3] and len(row[3]) > 200 else (row[3] or "")
        print(f"- {row[0]} ({row[2]})\n  {row[1]}\n  Snippet: {snippet}\n")

def main():
    init_db()
    articles = fetch_articles()
    if articles:
        save_articles(articles)
    else:
        print("No articles found or failed to fetch.")
    show_recent_articles()

if __name__ == "__main__":
    main()