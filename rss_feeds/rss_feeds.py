"""
title: Enhanced RSS News Filter with Web Scraped Dates
description: RSS news with async fetching, caching, inline links, and date scraping from webpages when RSS date is missing.
author: pkeffect
author_url: https://github.com/pkeffect/
project_url: https://github.com/pkeffect/open-webui-tools/tree/main/rss_feeds
funding_url: https://github.com/open-webui
required_open_webui_version: 0.6.0
version: 0.0.1
date: 2025-05-23
license: MIT
changelog:
  - 0.0.1 - initial upload

requirements: requests
"""

import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Callable, Any, Awaitable
from pydantic import BaseModel, Field
from urllib.parse import urlparse
import time

# Optional async imports - will fallback if not available
try:
    import asyncio
    import aiohttp

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    asyncio = None
    aiohttp = None

# Attempt to import dateutil for robust date parsing
try:
    from dateutil import parser as dateutil_parser

    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    dateutil_parser = None

# BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None


class Filter:
    class Valves(BaseModel):
        rss_url: str = Field(
            default="https://feeds.bbci.co.uk/news/world/rss.xml,http://rss.cnn.com/rss/cnn_topstories.rss,https://abcnews.go.com/abcnews/topstories",
            description="Comma-separated RSS feed URLs.",  # Simplified description
        )
        # additional_feeds: str = Field(default="") # REMOVED
        enabled: bool = Field(default=True)
        show_debug: bool = Field(default=True)
        show_detailed_status: bool = Field(default=True)
        max_articles_per_feed: int = Field(default=7)
        max_total_articles_display: int = Field(default=10)
        article_description_length: int = Field(default=350)
        max_article_age_days: int = Field(default=2)
        timeout_seconds: int = Field(default=30)
        show_links: bool = Field(default=True)
        enable_concurrent: bool = Field(default=True)
        max_workers: int = Field(default=3)
        per_feed_timeout: int = Field(default=15)
        enable_date_scraping: bool = Field(default=True)
        scrape_timeout_seconds: int = Field(default=7)
        enable_cache: bool = Field(default=True)
        cache_ttl_seconds: int = Field(default=180)
        cache_stale_if_error: bool = Field(default=True)
        enable_deduplication: bool = Field(default=True)
        enable_relevance_scoring: bool = Field(default=True)
        min_relevance_score: float = Field(default=0.0)

    def __init__(self):
        self.valves = self.Valves()
        self.processing_news = False
        self._cache: Dict[str, str] = {}
        self._page_cache: Dict[str, str] = {}
        self._page_cache_timestamps: Dict[str, float] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self.script_version = "1.5.5"
        if not BS4_AVAILABLE and self.valves.enable_date_scraping:
            self._log(
                "BeautifulSoup4 (bs4) is not installed, but date scraping is enabled. Scraping will be skipped. Please install with 'pip install beautifulsoup4 lxml'.",
                level="CRITICAL",
            )

    def _log(self, message: str, level: str = "DEBUG"):
        if self.valves.show_debug or level in ["ERROR", "WARNING", "CRITICAL", "INFO"]:
            print(f"🔍 RSS Filter ({self.script_version}) [{level}]: {message}")

    async def _emit_status(
        self, __event_emitter__, description: str, done: bool = False
    ):
        if __event_emitter__ and self.valves.show_detailed_status:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": description, "done": done, "hidden": False},
                }
            )

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        # ... (no changes, same as 1.5.4)
        if not date_str or date_str.lower() in ["no date", "unknown date"]:
            self._log(
                f"Date string is empty or indicates no date: '{date_str}'",
                level="DEBUG",
            )
            return None
        self._log(f"Attempting to parse date string: '{date_str}'", level="DEBUG")
        dt = None
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %Z",
        ]
        for fmt in formats:
            try:
                temp_date_str = date_str
                if ("%z" in fmt or fmt.endswith("Z")) and temp_date_str.endswith("Z"):
                    if "%z" in fmt:
                        temp_date_str = temp_date_str[:-1] + "+0000"
                if (
                    ".%f" in fmt
                    and "." not in temp_date_str.split("+")[0].split("-")[0]
                ):
                    temp_fmt = fmt.replace(".%f", "")
                    try:
                        dt = datetime.strptime(temp_date_str, temp_fmt)
                        self._log(
                            f"Parsed with strptime format '{temp_fmt}' (μs omitted): {dt}",
                            level="DEBUG",
                        )
                        break
                    except ValueError:
                        continue
                dt = datetime.strptime(temp_date_str, fmt)
                self._log(f"Parsed with strptime format '{fmt}': {dt}", level="DEBUG")
                break
            except ValueError:
                continue
        if dt is None and DATEUTIL_AVAILABLE and dateutil_parser:
            self._log(
                f"Falling back to dateutil.parser for '{date_str}'", level="DEBUG"
            )
            try:
                dt = dateutil_parser.parse(date_str)
                self._log(f"Parsed with dateutil.parser: {dt}", level="DEBUG")
            except Exception as e:
                self._log(
                    f"dateutil.parser failed for '{date_str}': {e}", level="WARNING"
                )
                dt = None
        elif dt is None and not DATEUTIL_AVAILABLE:
            self._log("dateutil.parser not available.", level="INFO")
        if dt:
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            self._log(f"Final parsed UTC datetime: {dt.isoformat()}", level="DEBUG")
            return dt
        self._log(
            f"Failed to parse date string: '{date_str}' after all attempts.",
            level="WARNING",
        )
        return None

    def _format_date(self, parsed_dt: Optional[datetime]) -> str:
        # ... (no changes, same as 1.5.4)
        if parsed_dt:
            return parsed_dt.strftime("%b %d, %Y")
        return "Unknown date"

    def _get_time_ago(self, parsed_dt: Optional[datetime]) -> str:
        # ... (no changes, same as 1.5.4)
        if parsed_dt:
            now_utc = datetime.now(timezone.utc)
            if now_utc.year < 2024:
                self._log(
                    f"CRITICAL SYSTEM TIME WARNING: Server's current year is {now_utc.year}. Time-based filtering will be unreliable!",
                    level="CRITICAL",
                )
            diff = now_utc - parsed_dt
            if diff.total_seconds() < 0:
                return parsed_dt.strftime("%b %d, %Y (%Z)")
            if diff.total_seconds() < 60:
                return "just now"
            minutes = int(diff.total_seconds() / 60)
            if minutes < 60:
                return f"{minutes} min ago"
            hours = int(minutes / 60)
            if hours < 24:
                return f"{hours} hr ago"
            days = int(hours / 24)
            return f"{days} day{'s' if days != 1 else ''} ago"
        return "recently"

    def _get_cached_rss_content(self, feed_url: str) -> Optional[str]:
        # ... (no changes, same as 1.5.4)
        if not self.valves.enable_cache:
            return None
        if feed_url in self._cache:
            age = time.time() - self._cache_timestamps.get(feed_url, 0)
            if age < self.valves.cache_ttl_seconds:
                self._log(
                    f"Cache HIT for RSS {urlparse(feed_url).netloc} (age: {age:.1f}s)",
                    level="INFO",
                )
                return self._cache[feed_url]
            self._log(
                f"Cache EXPIRED for RSS {urlparse(feed_url).netloc} (age: {age:.1f}s)",
                level="INFO",
            )
        return None

    def _set_cached_rss_content(self, feed_url: str, content: str):
        # ... (no changes, same as 1.5.4)
        if not self.valves.enable_cache:
            return
        self._cache[feed_url] = content
        self._cache_timestamps[feed_url] = time.time()
        self._log(f"Cache SET for RSS {urlparse(feed_url).netloc}", level="INFO")

    def _scrape_date_from_url(
        self, article_url: str, source_domain: str
    ) -> Optional[datetime]:
        # ... (no changes, same as 1.5.4)
        if (
            not self.valves.enable_date_scraping
            or not BS4_AVAILABLE
            or not article_url
            or article_url == "No link"
        ):
            return None
        if (
            article_url in self._page_cache
            and (time.time() - self._page_cache_timestamps.get(article_url, 0)) < 60
        ):
            self._log(f"Scrape Cache HIT for page: {article_url}", level="DEBUG")
            html_content = self._page_cache[article_url]
        else:
            self._log(f"Scraping date from URL: {article_url}", level="INFO")
            try:
                headers = {
                    "User-Agent": f"RSSNewsFilterDateScraper/{self.script_version}"
                }
                response = requests.get(
                    article_url,
                    timeout=self.valves.scrape_timeout_seconds,
                    headers=headers,
                    allow_redirects=True,
                )
                response.raise_for_status()
                html_content = response.text
                self._page_cache[article_url] = html_content
                self._page_cache_timestamps[article_url] = time.time()
            except requests.exceptions.RequestException as e:
                self._log(
                    f"Failed to fetch article page {article_url} for date scraping: {e}",
                    level="WARNING",
                )
                return None
        soup = BeautifulSoup(html_content, "lxml")
        scraped_date_str = None
        meta_selectors = [
            ("meta[property='article:published_time']", "content"),
            ("meta[name='cXenseParse:recs:publishtime']", "content"),
            ("meta[name='pubdate']", "content"),
            ("meta[name='sailthru.date']", "content"),
            ("meta[property='og:updated_time']", "content"),
            ("meta[name='date']", "content"),
        ]
        for selector, attr_name in meta_selectors:
            tag = soup.select_one(selector)
            if tag and tag.get(attr_name):
                scraped_date_str = tag.get(attr_name)
                self._log(
                    f"Found date via meta tag '{selector}': {scraped_date_str}",
                    level="DEBUG",
                )
                break
        if not scraped_date_str:
            time_tag = soup.select_one("time[datetime]")
            if time_tag and time_tag.get("datetime"):
                scraped_date_str = time_tag.get("datetime")
                self._log(
                    f"Found date via <time datetime>: {scraped_date_str}", level="DEBUG"
                )
            elif time_tag and time_tag.string:
                scraped_date_str = time_tag.string.strip()
                self._log(
                    f"Found date via <time> text: {scraped_date_str}", level="DEBUG"
                )
        if not scraped_date_str:
            if "bbc.com" in source_domain or "bbc.co.uk" in source_domain:
                bbc_time = soup.find("time", {"data-testid": "timestamp"})
                if bbc_time and bbc_time.get("datetime"):
                    scraped_date_str = bbc_time.get("datetime")
                elif bbc_time and bbc_time.string:
                    scraped_date_str = bbc_time.string.strip()
                self._log(
                    f"Attempted BBC specific scrape: {scraped_date_str}", level="DEBUG"
                )
            elif "cnn.com" in source_domain:
                cnn_timestamp_div = soup.select_one(
                    'div.timestamp, .metadata [data- meerdere-versions=""]'
                )
                if cnn_timestamp_div:
                    scraped_date_str = cnn_timestamp_div.text.strip()
                    scraped_date_str = re.sub(
                        r"^(Updated|Published)\s*",
                        "",
                        scraped_date_str,
                        flags=re.IGNORECASE,
                    )
                self._log(
                    f"Attempted CNN specific scrape: {scraped_date_str}", level="DEBUG"
                )
            elif "abcnews.go.com" in source_domain:
                abc_time_div = soup.select_one("div.TimeStamp__Date, .xvlfTak")
                if abc_time_div:
                    scraped_date_str = abc_time_div.text.strip()
                self._log(
                    f"Attempted ABCNews specific scrape: {scraped_date_str}",
                    level="DEBUG",
                )
        if not scraped_date_str:
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            for script_tag in json_ld_scripts:
                try:
                    import json

                    data = json.loads(script_tag.string)
                    date_keys = ["datePublished", "dateCreated", "uploadDate"]
                    if isinstance(data, dict):
                        for key in date_keys:
                            if data.get(key):
                                scraped_date_str = data[key]
                                break
                    elif isinstance(data, list):
                        for item_data in data:
                            if isinstance(item_data, dict):
                                for key in date_keys:
                                    if item_data.get(key):
                                        scraped_date_str = item_data[key]
                                        break
                            if scraped_date_str:
                                break
                    if scraped_date_str:
                        self._log(
                            f"Found date via JSON-LD: {scraped_date_str}", level="DEBUG"
                        )
                        break
                except (json.JSONDecodeError, TypeError) as e:
                    self._log(f"Error parsing JSON-LD: {e}", level="DEBUG")
                    continue
        if scraped_date_str:
            parsed_scraped_date = self._parse_datetime(scraped_date_str)
            if parsed_scraped_date:
                self._log(
                    f"Successfully scraped and parsed date for {article_url}: {parsed_scraped_date.isoformat()}",
                    level="INFO",
                )
                return parsed_scraped_date
            else:
                self._log(
                    f"Scraped date string '{scraped_date_str}' but failed to parse it for {article_url}",
                    level="WARNING",
                )
        else:
            self._log(
                f"Could not find any date element to scrape on {article_url}",
                level="DEBUG",
            )
        return None

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        # ... (no changes, same as 1.5.4)
        if not self.valves.enable_deduplication:
            return articles
        seen_titles_normalized = set()
        seen_links = set()
        unique_articles = []
        self._log(
            f"Starting deduplication for {len(articles)} articles.", level="DEBUG"
        )
        for article in articles:
            normalized_title = " ".join(
                re.sub(r"[^\w\s]", "", article["title"].lower()).strip().split()
            )
            article_link = article.get("link", "No link")
            if article_link != "No link":
                if article_link in seen_links:
                    self._log(
                        f"Deduplicating (link): '{article['title'][:30]}...' Link: {article_link}",
                        level="DEBUG",
                    )
                    continue
                seen_links.add(article_link)
            if normalized_title in seen_titles_normalized:
                is_truly_duplicate = True
                if article_link != "No link":
                    pass
                if is_truly_duplicate:
                    self._log(
                        f"Deduplicating (title): '{article['title'][:30]}...'",
                        level="DEBUG",
                    )
                    continue
            seen_titles_normalized.add(normalized_title)
            unique_articles.append(article)
        if len(unique_articles) < len(articles):
            self._log(
                f"Deduplication: {len(articles)} -> {len(unique_articles)} articles",
                level="INFO",
            )
        return unique_articles

    def _parse_rss_content(self, content: str, source_name: str) -> List[Dict]:
        # ... (no changes, same as 1.5.4)
        self._log(
            f"Starting to parse RSS content for source: {source_name}", level="DEBUG"
        )
        articles = []
        source_domain = urlparse(
            source_name if "http" in source_name else f"http://{source_name}"
        ).netloc
        try:
            content = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&", content)
            content = "".join(
                c for c in content if ord(c) >= 32 or c in ("\t", "\n", "\r")
            )
            root = ET.fromstring(content)
            items = root.findall(".//item") or root.findall(
                "{http://www.w3.org/2005/Atom}entry"
            )
            self._log(
                f"Found {len(items)} item(s) in feed for {source_name}", level="DEBUG"
            )
            for i, item in enumerate(items[: self.valves.max_articles_per_feed]):
                title_elem = item.find("title")
                raw_title = (
                    title_elem.text.strip()
                    if title_elem is not None and title_elem.text
                    else "No title"
                )
                link_text = "No link"
                link_elem = item.find("link")
                if link_elem is None:
                    atom_links = item.findall(
                        "{http://www.w3.org/2005/Atom}link[@rel='alternate'][@type='text/html']"
                    )
                    if atom_links:
                        link_elem = atom_links[0]
                if link_elem is not None:
                    href_attr = link_elem.get("href")
                    link_elem_text = link_elem.text
                    if href_attr:
                        link_text = href_attr.strip()
                    elif link_elem_text:
                        link_text = link_elem_text.strip()
                pub_date_elem = (
                    item.find("pubDate")
                    or item.find("{http://www.w3.org/2005/Atom}published")
                    or item.find("{http://www.w3.org/2005/Atom}updated")
                )
                raw_date_text_rss = (
                    pub_date_elem.text.strip()
                    if pub_date_elem is not None and pub_date_elem.text
                    else None
                )
                self._log(
                    f"  Item '{raw_title[:30]}...': RSS Date='{raw_date_text_rss}', Link='{link_text}'",
                    level="DEBUG",
                )
                desc_elem = (
                    item.find("description")
                    or item.find("{http://www.w3.org/2005/Atom}summary")
                    or item.find("{http://www.w3.org/2005/Atom}content")
                )
                description = ""
                if desc_elem is not None and desc_elem.text:
                    description = re.sub(
                        r"\s+", " ", re.sub(r"<[^>]+>", "", desc_elem.text.strip())
                    ).strip()
                    if len(description) > self.valves.article_description_length:
                        description = (
                            description[: self.valves.article_description_length - 3]
                            + "..."
                        )
                if raw_title != "No title":
                    parsed_dt = None
                    if raw_date_text_rss:
                        parsed_dt = self._parse_datetime(raw_date_text_rss)
                        if parsed_dt:
                            self._log(
                                f"  Parsed RSS DT for '{raw_title[:30]}...': {parsed_dt.isoformat()}",
                                level="DEBUG",
                            )
                    if (
                        not parsed_dt
                        and self.valves.enable_date_scraping
                        and link_text != "No link"
                    ):
                        self._log(
                            f"Attempting to scrape date for '{raw_title[:30]}...' from {link_text}",
                            level="INFO",
                        )
                        scraped_dt = self._scrape_date_from_url(
                            link_text, source_domain
                        )
                        if scraped_dt:
                            parsed_dt = scraped_dt
                            self._log(
                                f"  Using SCRAPED date for '{raw_title[:30]}...': {parsed_dt.isoformat()}",
                                level="INFO",
                            )
                    article_info = {
                        "title": raw_title,
                        "link": link_text,
                        "description": description,
                        "source": source_name,
                        "parsed_datetime": parsed_dt,
                        "time_ago": self._get_time_ago(parsed_dt),
                        "formatted_date": self._format_date(parsed_dt),
                    }
                    log_info = {
                        k: (v.isoformat() if isinstance(v, datetime) else v)
                        for k, v in article_info.items()
                    }
                    self._log(
                        f"  Final Processed article_info: {log_info}", level="DEBUG"
                    )
                    articles.append(article_info)
                else:
                    self._log(
                        f"  Skipping item for {source_name} due to missing title.",
                        level="WARNING",
                    )
        except ET.ParseError as e:
            self._log(
                f"XML Parse error for {source_name}: {e}. Content snippet: '{content[:300]}'",
                level="ERROR",
            )
        except Exception as e:
            self._log(f"General Parse error for {source_name}: {e}", level="ERROR")
        self._log(
            f"Finished parsing for {source_name}, got {len(articles)} articles.",
            level="DEBUG",
        )
        return articles

    async def _fetch_feed_async(
        self, session, feed_url: str, idx: int, total: int, emitter
    ) -> Dict:
        # ... (no changes, same as 1.5.4)
        source_name = urlparse(feed_url).netloc
        self._log(
            f"Async fetch attempt for {feed_url} ({idx+1}/{total})", level="DEBUG"
        )
        cached_content = self._get_cached_rss_content(feed_url)
        if cached_content:
            return {
                "source": source_name,
                "articles": self._parse_rss_content(cached_content, source_name),
                "success": True,
                "cached": True,
                "error": None,
            }
        await self._emit_status(emitter, f"📰 Fetching {idx+1}/{total}: {source_name}")
        headers = {
            "User-Agent": f"RSSNewsFilter/{self.script_version} (Python; +https://github.com/your-repo)"
        }
        try:
            async with session.get(
                feed_url,
                timeout=aiohttp.ClientTimeout(total=self.valves.per_feed_timeout),
                headers=headers,
                allow_redirects=True,
            ) as response:
                self._log(
                    f"Response status for {feed_url}: {response.status}", level="DEBUG"
                )
                if response.status == 200:
                    content = await response.text()
                    self._set_cached_rss_content(feed_url, content)
                    return {
                        "source": source_name,
                        "articles": self._parse_rss_content(content, source_name),
                        "success": True,
                        "cached": False,
                        "error": None,
                    }
                error_msg = f"HTTP {response.status}"
                if self.valves.cache_stale_if_error and feed_url in self._cache:
                    self._log(
                        f"Using stale cache for {source_name} due to {error_msg}",
                        level="WARNING",
                    )
                    return {
                        "source": source_name,
                        "articles": self._parse_rss_content(
                            self._cache[feed_url], source_name
                        ),
                        "success": True,
                        "error": f"{error_msg} (using stale cache)",
                        "cached": True,
                    }
                return {
                    "source": source_name,
                    "articles": [],
                    "success": False,
                    "error": error_msg,
                    "cached": False,
                }
        except asyncio.TimeoutError:
            error_str = "Timeout"
            self._log(f"Timeout fetching {source_name}", level="WARNING")
        except aiohttp.ClientError as e:
            error_str = f"ClientError: {type(e).__name__}"
            self._log(f"ClientError fetching {source_name}: {e}", level="WARNING")
        except Exception as e:
            error_str = str(e)
            self._log(f"Generic error fetching {source_name}: {e}", level="ERROR")
        if self.valves.cache_stale_if_error and feed_url in self._cache:
            self._log(
                f"Using stale cache for {source_name} due to error: {error_str}",
                level="WARNING",
            )
            return {
                "source": source_name,
                "articles": self._parse_rss_content(self._cache[feed_url], source_name),
                "success": True,
                "error": f"{error_str} (using stale cache)",
                "cached": True,
            }
        return {
            "source": source_name,
            "articles": [],
            "success": False,
            "error": error_str,
            "cached": False,
        }

    async def _fetch_all_feeds_async(self, feed_urls: List[str], emitter) -> tuple:
        # ... (no changes, same as 1.5.4)
        all_articles, successful_sources = [], []
        semaphore = asyncio.Semaphore(self.valves.max_workers)

        async def fetch_with_sem(session, url, i, total, em):
            async with semaphore:
                return await self._fetch_feed_async(session, url, i, total, em)

        conn = aiohttp.TCPConnector(limit_per_host=self.valves.max_workers)
        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [
                fetch_with_sem(session, url, i, len(feed_urls), emitter)
                for i, url in enumerate(feed_urls)
            ]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.valves.timeout_seconds,
                )
            except asyncio.TimeoutError:
                self._log(
                    f"Overall fetch timeout after {self.valves.timeout_seconds}s. Processing completed tasks.",
                    level="WARNING",
                )
                results = []
                for i_task, task in enumerate(tasks):
                    if task.done() and not task.cancelled():
                        try:
                            results.append(task.result())
                        except Exception as e_res:
                            self._log(
                                f"Error retrieving result for task {i_task} ({feed_urls[i_task]}): {e_res}",
                                level="ERROR",
                            )
                            results.append(
                                {
                                    "source": urlparse(feed_urls[i_task]).netloc,
                                    "articles": [],
                                    "success": False,
                                    "error": f"Task Error: {str(e_res)[:50]}",
                                    "cached": False,
                                }
                            )
                    else:
                        if not task.done():
                            task.cancel()
                        self._log(
                            f"Task {i_task} ({feed_urls[i_task]}) was cancelled or timed out individually.",
                            level="DEBUG",
                        )
                        results.append(
                            {
                                "source": urlparse(feed_urls[i_task]).netloc,
                                "articles": [],
                                "success": False,
                                "error": "Timeout/Cancelled",
                                "cached": False,
                            }
                        )
            for res in results:
                if isinstance(res, Exception):
                    self._log(
                        f"Unhandled exception from asyncio.gather task: {res}",
                        level="ERROR",
                    )
                    await self._emit_status(
                        emitter,
                        f"❌ Unknown Source: Gather task error - {str(res)[:50]}",
                    )
                    continue
                source_display = res.get("source", "Unknown Source")
                if res.get("success"):
                    all_articles.extend(res["articles"])
                    if res["articles"] or res.get("cached"):
                        successful_sources.append(source_display)
                    cache_indicator = " (cached)" if res.get("cached") else ""
                    stale_info = ""
                    if res.get("cached") and "stale cache" in (res.get("error") or ""):
                        stale_info = f" (stale: {res['error'].replace('(using stale cache)', '').strip()})"
                    msg_level = "INFO" if not stale_info else "WARNING"
                    self._log(
                        f"✅ {source_display}: {len(res['articles'])} articles{cache_indicator}{stale_info}",
                        level=msg_level,
                    )
                    await self._emit_status(
                        emitter,
                        f"✅ {source_display}: {len(res['articles'])} articles{cache_indicator}{stale_info}",
                    )
                else:
                    err_msg = res.get("error", "Unknown error")
                    self._log(
                        f"❌ {source_display}: Fetch failed - {err_msg}",
                        level="WARNING",
                    )
                    await self._emit_status(emitter, f"❌ {source_display}: {err_msg}")
        return all_articles, successful_sources

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> dict:
        if not self.valves.enabled:
            return body
        messages = body.get("messages", [])
        if not messages:
            return body
        user_msg_content = ""
        if messages[-1].get("content"):
            if isinstance(messages[-1]["content"], str):
                user_msg_content = messages[-1]["content"].lower()
            elif isinstance(messages[-1]["content"], list):
                for item_content in messages[-1]["content"]:
                    if (
                        isinstance(item_content, dict)
                        and item_content.get("type") == "text"
                    ):
                        user_msg_content = item_content.get("text", "").lower()
                        break
        if not user_msg_content:
            return body
        news_keywords = [
            "news",
            "headlines",
            "latest",
            "breaking",
            "happening",
            "what's new",
            "updates",
            "current events",
            "story",
            "stories",
        ]
        is_news_q = any(word in user_msg_content for word in news_keywords) or (
            (
                "what" in user_msg_content
                or "tell me" in user_msg_content
                or "give me" in user_msg_content
            )
            and any(
                kw in user_msg_content
                for kw in ["happening", "going on", "developments"]
            )
        )
        if not is_news_q:
            return body
        self.processing_news = True
        self._log("NEWS QUERY DETECTED - Fetching RSS...", level="INFO")
        await self._emit_status(
            __event_emitter__, "🔍 News query detected - Starting RSS fetch..."
        )

        # UPDATED feed URL collection
        feed_urls = []
        if self.valves.rss_url and self.valves.rss_url.strip():
            feed_urls.extend(
                [url.strip() for url in self.valves.rss_url.split(",") if url.strip()]
            )

        feed_urls = sorted(
            list(set(f for f in feed_urls if urlparse(f).scheme and urlparse(f).netloc))
        )
        self._log(f"Final list of feed URLs to process: {feed_urls}", level="DEBUG")

        if not feed_urls:
            self._log("No valid RSS feed URLs configured.", level="WARNING")
            await self._emit_status(
                __event_emitter__, "⚠️ No RSS feed URLs configured.", done=True
            )
            return body

        now_for_check = datetime.now(timezone.utc)
        self._log(
            f"Server's current UTC time for recency check: {now_for_check.isoformat()}",
            level="INFO",
        )
        if now_for_check.year < 2024:
            self._log(
                f"CRITICAL SYSTEM TIME WARNING: Server's current year is {now_for_check.year}. This will likely cause issues with recency filtering. Please check server time configuration.",
                level="CRITICAL",
            )
            await self._emit_status(
                __event_emitter__,
                f"⚠️ Server time ({now_for_check.year}) may be incorrect, affecting news recency.",
            )

        await self._emit_status(
            __event_emitter__, f"📡 Fetching from {len(feed_urls)} RSS sources..."
        )
        total_start_time = time.time()
        all_articles_raw, successful_sources = [], []
        use_async = ASYNC_AVAILABLE and self.valves.enable_concurrent
        if use_async:
            # ... (Async fetch logic - same as 1.5.4)
            self._log("Using ASYNC concurrent fetching", level="INFO")
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                all_articles_raw, successful_sources = (
                    await self._fetch_all_feeds_async(feed_urls, __event_emitter__)
                )
            except Exception as e_async_main:
                self._log(
                    f"Main async fetching process failed: {e_async_main}", level="ERROR"
                )
                await self._emit_status(
                    __event_emitter__,
                    f"❌ Async fetching error: {str(e_async_main)[:100]}",
                    done=True,
                )
                all_articles_raw, successful_sources = [], []
        else:
            # ... (Sync fetch logic - same as 1.5.4)
            self._log(
                f"Using SYNCHRONOUS fetching (Async available: {ASYNC_AVAILABLE}, Concurrent enabled: {self.valves.enable_concurrent})",
                level="INFO",
            )
            headers = {
                "User-Agent": f"RSSNewsFilter/{self.script_version} (Python; +https://github.com/your-repo)"
            }
            for i, feed_url in enumerate(feed_urls):
                source_name = urlparse(feed_url).netloc
                await self._emit_status(
                    __event_emitter__,
                    f"📰 Fetching {i+1}/{len(feed_urls)}: {source_name} (sync)",
                )
                self._log(f"Sync fetch attempt for {feed_url}", level="DEBUG")
                cached_content = self._get_cached_rss_content(feed_url)
                if cached_content:
                    articles_from_feed = self._parse_rss_content(
                        cached_content, source_name
                    )
                    if articles_from_feed:
                        all_articles_raw.extend(articles_from_feed)
                        successful_sources.append(source_name)
                    await self._emit_status(
                        __event_emitter__,
                        f"✅ {source_name}: {len(articles_from_feed)} articles (cached)",
                    )
                    continue
                try:
                    current_timeout = (
                        self.valves.per_feed_timeout
                        if len(feed_urls) > 1
                        else self.valves.timeout_seconds
                    )
                    resp = requests.get(
                        feed_url,
                        timeout=current_timeout,
                        headers=headers,
                        allow_redirects=True,
                    )
                    self._log(
                        f"Sync response status for {feed_url}: {resp.status_code}",
                        level="DEBUG",
                    )
                    if resp.status_code == 200:
                        self._set_cached_rss_content(feed_url, resp.text)
                        articles_from_feed = self._parse_rss_content(
                            resp.text, source_name
                        )
                        if articles_from_feed:
                            all_articles_raw.extend(articles_from_feed)
                            successful_sources.append(source_name)
                        await self._emit_status(
                            __event_emitter__,
                            f"✅ {source_name}: {len(articles_from_feed)} articles",
                        )
                    else:
                        error_msg = f"HTTP {resp.status_code}"
                        if self.valves.cache_stale_if_error and feed_url in self._cache:
                            articles_from_feed = self._parse_rss_content(
                                self._cache[feed_url], source_name
                            )
                            if articles_from_feed:
                                all_articles_raw.extend(articles_from_feed)
                                successful_sources.append(source_name)
                            await self._emit_status(
                                __event_emitter__,
                                f"✅ {source_name}: {len(articles_from_feed)} (stale: {error_msg})",
                            )
                        else:
                            await self._emit_status(
                                __event_emitter__, f"❌ {source_name}: {error_msg}"
                            )
                except requests.exceptions.Timeout:
                    self._log(f"Sync timeout fetching {feed_url}", level="WARNING")
                    if self.valves.cache_stale_if_error and feed_url in self._cache:
                        articles_from_feed = self._parse_rss_content(
                            self._cache[feed_url], source_name
                        )
                        if articles_from_feed:
                            all_articles_raw.extend(articles_from_feed)
                            successful_sources.append(source_name)
                        await self._emit_status(
                            __event_emitter__,
                            f"✅ {source_name}: {len(articles_from_feed)} (stale: Timeout)",
                        )
                    else:
                        await self._emit_status(
                            __event_emitter__, f"❌ {source_name}: Timeout"
                        )
                except Exception as e_sync:
                    error_str = str(e_sync)
                    self._log(
                        f"Sync error fetching {feed_url}: {error_str}", level="ERROR"
                    )
                    if self.valves.cache_stale_if_error and feed_url in self._cache:
                        articles_from_feed = self._parse_rss_content(
                            self._cache[feed_url], source_name
                        )
                        if articles_from_feed:
                            all_articles_raw.extend(articles_from_feed)
                            successful_sources.append(source_name)
                        await self._emit_status(
                            __event_emitter__,
                            f"✅ {source_name}: {len(articles_from_feed)} (stale: {error_str[:30]})",
                        )
                    else:
                        await self._emit_status(
                            __event_emitter__,
                            f"❌ {source_name}: Error {error_str[:30]}",
                        )

        total_time = time.time() - total_start_time
        unique_successful_sources = sorted(
            list(set(s for s in successful_sources if s))
        )
        self._log(
            f"Total articles fetched before any filtering: {len(all_articles_raw)} from {len(unique_successful_sources)} sources.",
            level="INFO",
        )

        if (
            self.valves.show_debug and all_articles_raw
        ):  # ... (Pre-filter logging - same as 1.5.4)
            self._log("--- Parsed Dates (RSS & Scraped) Pre-Filter ---", level="DEBUG")
            for i, article in enumerate(all_articles_raw):
                dt_str = (
                    article.get("parsed_datetime").isoformat()
                    if article.get("parsed_datetime")
                    else "None"
                )
                self._log(
                    f"  Article {i+1} ('{article['title'][:20]}...'): Final Parsed DateTime = {dt_str}",
                    level="DEBUG",
                )
            self._log("---------------------------------------------", level="DEBUG")

        all_articles_filtered = list(all_articles_raw)
        if all_articles_filtered:
            # ... (Filtering logic: Recency, Dedupe, Relevance, MaxTotal - same as 1.5.4)
            if self.valves.max_article_age_days > 0:
                now_utc_filter = datetime.now(timezone.utc)
                cutoff_date = now_utc_filter - timedelta(
                    days=self.valves.max_article_age_days
                )
                self._log(
                    f"Recency Filter: Max age {self.valves.max_article_age_days} days. Current UTC: {now_utc_filter.isoformat()}. Cutoff Date (inclusive): {cutoff_date.isoformat()}",
                    level="INFO",
                )
                original_count = len(all_articles_filtered)
                articles_after_recency = []
                for article in all_articles_filtered:
                    article_dt = article.get("parsed_datetime")
                    if article_dt:
                        if article_dt >= cutoff_date:
                            articles_after_recency.append(article)
                        else:
                            self._log(
                                f"Filtering out OLD article: '{article['title'][:30]}...' (Date: {article_dt.isoformat()}, Cutoff: {cutoff_date.isoformat()})",
                                level="DEBUG",
                            )
                    else:
                        self._log(
                            f"Filtering out article with UNPARSED/UNKNOWN date during recency check: '{article['title'][:30]}...'",
                            level="WARNING",
                        )
                if len(articles_after_recency) < original_count:
                    self._log(
                        f"Recency filter : {original_count} -> {len(articles_after_recency)} articles",
                        level="INFO",
                    )
                    await self._emit_status(
                        __event_emitter__,
                        f"🗓️ Filtered by recency (max {self.valves.max_article_age_days} days): {original_count} -> {len(articles_after_recency)} articles",
                    )
                all_articles_filtered = articles_after_recency
            if not all_articles_filtered:
                self._log("No articles remained after recency filter.", level="INFO")
            if self.valves.enable_deduplication and all_articles_filtered:
                original_count = len(all_articles_filtered)
                all_articles_filtered = self._deduplicate_articles(
                    all_articles_filtered
                )
                if len(all_articles_filtered) < original_count:
                    await self._emit_status(
                        __event_emitter__,
                        f"📰 Deduplicated: {original_count} -> {len(all_articles_filtered)}",
                    )
            if self.valves.enable_relevance_scoring and all_articles_filtered:
                stop_words = [
                    "news",
                    "latest",
                    "what",
                    "is",
                    "the",
                    "a",
                    "an",
                    "tell",
                    "me",
                    "about",
                    "happening",
                    "breaking",
                    "give",
                    "updates",
                    "current",
                    "events",
                    "whats",
                    "what's",
                    "on",
                    "in",
                    "for",
                    "of",
                    "show",
                    "me",
                    "and",
                    "or",
                    "but",
                    "can",
                    "you",
                    "find",
                ]
                query_words = list(
                    set(
                        w
                        for w in user_msg_content.split()
                        if len(w) > 2 and w not in stop_words
                    )
                )
                if query_words:
                    self._log(
                        f"Scoring relevance for query words: {query_words}",
                        level="INFO",
                    )
                    await self._emit_status(
                        __event_emitter__,
                        f"💡 Scoring relevance for: {', '.join(query_words)}",
                    )
                    for article_idx, article in enumerate(all_articles_filtered):
                        article["relevance_score"] = self._calculate_relevance_score(
                            article, query_words
                        )
                    all_articles_filtered.sort(
                        key=lambda x: x.get("relevance_score", 0.0), reverse=True
                    )
                    if self.valves.min_relevance_score > 0.0:
                        c_before = len(all_articles_filtered)
                        all_articles_filtered = [
                            a
                            for a in all_articles_filtered
                            if a.get("relevance_score", 0.0)
                            >= self.valves.min_relevance_score
                        ]
                        if len(all_articles_filtered) < c_before:
                            self._log(
                                f"Relevance filter: {c_before} -> {len(all_articles_filtered)} (min score: {self.valves.min_relevance_score})",
                                level="INFO",
                            )
                            await self._emit_status(
                                __event_emitter__,
                                f"📉 Relevance filter: {c_before} -> {len(all_articles_filtered)}",
                            )
                else:
                    self._log(
                        "No specific query words for relevance. Sorting by date.",
                        level="INFO",
                    )
                    all_articles_filtered.sort(
                        key=lambda x: x.get("parsed_datetime")
                        or datetime.min.replace(tzinfo=timezone.utc),
                        reverse=True,
                    )
            elif all_articles_filtered:
                self._log("Relevance scoring disabled. Sorting by date.", level="INFO")
                all_articles_filtered.sort(
                    key=lambda x: x.get("parsed_datetime")
                    or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True,
                )
            if (
                all_articles_filtered
                and len(all_articles_filtered) > self.valves.max_total_articles_display
            ):
                self._log(
                    f"Trimming articles from {len(all_articles_filtered)} to {self.valves.max_total_articles_display}",
                    level="INFO",
                )
                await self._emit_status(
                    __event_emitter__,
                    f"✂️ Trimming articles from {len(all_articles_filtered)} to {self.valves.max_total_articles_display}",
                )
                all_articles_filtered = all_articles_filtered[
                    : self.valves.max_total_articles_display
                ]
            self._log(
                f"Final number of articles to display: {len(all_articles_filtered)}",
                level="DEBUG",
            )

        if all_articles_filtered:
            fetch_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            news_content_header = f"""🔴 LIVE RSS DATA INJECTED 🔴
VERIFICATION: This is REAL news data fetched from RSS feeds at {fetch_time_str}
📰 CURRENT NEWS HEADLINES ({len(all_articles_filtered)} articles from {len(unique_successful_sources)} sources, max {self.valves.max_article_age_days} days old):
"""
            article_entries = []
            for idx, article in enumerate(all_articles_filtered):
                entry = f"**{article['title']}** ({article['time_ago']})"
                if article["description"]:
                    entry += f"\n    {article['description']}"

                info_line_parts = []
                if self.valves.show_links and article["link"] != "No link":
                    info_line_parts.append(f"Source: {article['link']}")
                else:
                    info_line_parts.append(
                        f"Source: {article['source']} (link not available for this item)"
                    )

                if article["formatted_date"] != "Unknown date":
                    info_line_parts.append(f"Published: {article['formatted_date']}")
                else:
                    info_line_parts.append("Published: date unknown")

                entry += f"\n    *{' - '.join(info_line_parts)}*"

                article_entries.append(entry)

            news_content_body = "\n\n".join(article_entries)

            llm_instructions = f"""
🚨 CRITICAL INSTRUCTIONS FOR LLM:
- You MUST start your response with "✅ RSS FEED ACTIVE - Current news from {len(unique_successful_sources)} sources ({len(all_articles_filtered)} articles total, max {self.valves.max_article_age_days} days old)"
- Refer to articles by their **title**. If titles are similar, you can clarify by mentioning the source URL or time context.
- For each article discussed, provide a comprehensive summary incorporating its title, key information from its description (if available), and its relative time context (e.g., "{all_articles_filtered[0]['time_ago'] if all_articles_filtered else 'recently'}").
- The article source (as a direct URL) and publication date are provided in italics below each article's description. Use this for context.
- Present information clearly.
- DO NOT make up any news stories. Only discuss the articles provided above.
- If no articles seem relevant to a very specific user query (beyond just "news"), state that general headlines were fetched and offer those, or ask for clarification.
"""
            system_msg_content = (
                news_content_header + "\n" + news_content_body + "\n" + llm_instructions
            )
            messages.insert(0, {"role": "system", "content": system_msg_content})
            body["messages"] = messages
            success_msg = f"✅ News loaded: {len(all_articles_filtered)} articles from {len(unique_successful_sources)} sources ({total_time:.1f}s)"
            await self._emit_status(__event_emitter__, success_msg, done=True)
            self._log(f"{success_msg} - RSS DATA INJECTED.", level="INFO")
            return body

        self._log(
            f"❌ No articles found/processed to display after {total_time:.1f}s from {len(feed_urls)} sources. Max age days: {self.valves.max_article_age_days}",
            level="WARNING",
        )
        await self._emit_status(
            __event_emitter__,
            f"❌ No recent articles found/processed after {total_time:.1f}s.",
            done=True,
        )
        failure_content = f"""🔴 RSS FEED FAILED OR NO RECENT ARTICLES FOUND/PROCESSED 🔴
Attempted to fetch news at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, but no suitable articles (max {self.valves.max_article_age_days} days old) were retrieved or processed.
This could be due to network issues, invalid RSS feed URLs, no content in the feeds, all articles being older than the configured recency limit, or dates not being found/scraped successfully.
Please check server time, feed URLs, and console logs for parsing/scraping errors.
🚨 CRITICAL: Respond with: "❌ RSS NEWS UNAVAILABLE - I could not retrieve any recent news articles (max {self.valves.max_article_age_days} days old) at this time. Please try again later or check the feed configurations."
Do NOT make up news."""
        messages.insert(0, {"role": "system", "content": failure_content})
        body["messages"] = messages
        self._log("❌ RSS FAILURE/NO RECENT ARTICLES MESSAGE INJECTED", level="WARNING")
        return body

    async def outlet(self, body: dict, __user__=None, __event_emitter__=None) -> dict:
        if self.processing_news:
            self._log("Resetting news processing state.", level="INFO")
        self.processing_news = False
        return body
