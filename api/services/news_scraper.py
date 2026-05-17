"""
News scraping service - fetches and parses news from multiple sources.
"""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from api.core.cache import cached
from api.core.logging import log


@cached("news", ttl=1800)  # Cache for 30 minutes
async def scrape_news(sources: list[str] | None = None, limit: int = 5) -> list[dict]:
    """
    Scrape news from multiple sources.
    
    Args:
        sources: List of news source URLs (defaults to HN and TechCrunch)
        limit: Maximum number of articles per source
    
    Returns:
        List of news articles with title, url, source
    """
    if sources is None:
        sources = [
            "https://news.ycombinator.com",
            "https://techcrunch.com"
        ]
    
    news_items = []
    
    for source in sources:
        try:
            articles = await _scrape_source(source, limit)
            news_items.extend(articles)
        except Exception as exc:
            log.error("news_scrape_failed", source=source, error=str(exc))
    
    log.info("news_scraped", total=len(news_items))
    return news_items[:limit * len(sources)]


async def _scrape_source(url: str, limit: int) -> list[dict]:
    """Scrape a single news source."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Source-specific selectors
            if "ycombinator.com" in url:
                return _parse_hackernews(soup, limit)
            elif "techcrunch.com" in url:
                return _parse_techcrunch(soup, limit)
            elif "reddit.com" in url:
                return _parse_reddit(soup, limit)
            else:
                return _parse_generic(soup, url, limit)
    
    except Exception as exc:
        log.error("source_scrape_failed", url=url, error=str(exc))
        return []


def _parse_hackernews(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Parse Hacker News."""
    articles = []
    
    # HN uses .titleline for story titles
    title_elements = soup.select('.titleline > a')
    
    for elem in title_elements[:limit]:
        title = elem.get_text().strip()
        href = elem.get('href', '')
        
        # Make relative URLs absolute
        if href.startswith('item?'):
            href = f"https://news.ycombinator.com/{href}"
        
        articles.append({
            "title": title,
            "url": href,
            "source": "Hacker News"
        })
    
    return articles


def _parse_techcrunch(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Parse TechCrunch."""
    articles = []
    
    # TechCrunch article links
    article_links = soup.select('h2 a, h3 a')
    
    for elem in article_links[:limit]:
        title = elem.get_text().strip()
        href = elem.get('href', '')
        
        if title and href and href.startswith('http'):
            articles.append({
                "title": title,
                "url": href,
                "source": "TechCrunch"
            })
    
    return articles


def _parse_reddit(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Parse Reddit."""
    articles = []
    
    # Reddit post titles
    post_elements = soup.select('[data-testid="post-container"] h3')
    
    for elem in post_elements[:limit]:
        title = elem.get_text().strip()
        # Find parent link
        link_elem = elem.find_parent('a')
        href = link_elem.get('href', '') if link_elem else ''
        
        if title and href:
            if not href.startswith('http'):
                href = f"https://reddit.com{href}"
            
            articles.append({
                "title": title,
                "url": href,
                "source": "Reddit"
            })
    
    return articles


def _parse_generic(soup: BeautifulSoup, source_url: str, limit: int) -> list[dict]:
    """Generic parser for unknown sources."""
    articles = []
    
    # Try common article selectors
    selectors = [
        'article h2 a',
        'article h3 a',
        '.post-title a',
        '.entry-title a',
        'h2 a',
        'h3 a'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:limit]:
                title = elem.get_text().strip()
                href = elem.get('href', '')
                
                if title and href:
                    # Make relative URLs absolute
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(source_url, href)
                    
                    articles.append({
                        "title": title,
                        "url": href,
                        "source": source_url.split('/')[2]  # Extract domain
                    })
            
            if articles:
                break
    
    return articles[:limit]


def format_news(news_items: list[dict]) -> str:
    """Format news items for display."""
    if not news_items:
        return "No news available."
    
    lines = []
    for item in news_items:
        lines.append(f"• <a href='{item['url']}'>{item['title']}</a>")
        lines.append(f"  <i>{item['source']}</i>")
    
    return "\n".join(lines)

# Made with Bob
