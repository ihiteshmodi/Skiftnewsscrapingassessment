# Skift News Scraper

This project is a robust web scraper for the [Skift News](https://skift.com/news/) website. It incrementally loads and stores news articles in a local SQLite database, handling duplicates and network errors.

## Features

- **Data Extraction**:  
  - This project scrapes the Skift News website directly [first page only] (no official API is available).
  - For each article, it extracts the URL, title, publication timestamp, source, and full article content.

- **Incremental Loading**:  
  - The scraper only fetches and stores new articles that have not been previously scraped [on the first page only], using the article URL as a unique identifier.

- **Schema Design**:  
  - Articles are stored in a SQLite database with the following schema:
    - `article_id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    - `url` (TEXT, UNIQUE)
    - `title` (TEXT)
    - `publication_timestamp` (TEXT)
    - `source` (TEXT)
    - `content` (TEXT)

- **Robustness**:  
  - Handles network errors, timeouts, and parsing errors gracefully.
  - Duplicate entries are avoided using a unique constraint on the article URL.
  - All exceptions are caught and logged; the script continues processing other articles.

## Usage

1. **Install dependencies**  
   ```
   pip install -r requirements.txt
   ```

2. **Run the scraper**  
   ```
   python skift_scraper.py
   ```
   - This will fetch the latest articles, store new ones in the database, and print the 5 most recent articles with a content snippet.


## Project Structure

- `skift_scraper.py` — Main scraper script.
- `skift_articles.db` — SQLite database (created automatically).
- `requirements.txt` — Python dependencies.

## Notes

- This project is for educational and assessment purposes.  
- Please respect the target website's robots.txt and terms of service.
