# 📰 Enhanced RSS News Filter with Web Scraped Dates

[![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

> 🚀 A powerful, feature-rich RSS news aggregator with intelligent date extraction, concurrent fetching, and smart filtering capabilities.

## ✨ Features

### 🔥 Core Capabilities
- **📡 Multi-Source RSS Aggregation** - Fetch from multiple RSS feeds simultaneously
- **⚡ Async Concurrent Fetching** - Lightning-fast parallel processing with configurable workers
- **🕰️ Intelligent Date Extraction** - Advanced date parsing with web scraping fallback
- **💾 Smart Caching System** - Built-in TTL caching with stale-if-error fallback
- **🔍 Content Deduplication** - Remove duplicate articles based on titles and links
- **📊 Relevance Scoring** - Intelligent article ranking based on query relevance
- **🗓️ Age Filtering** - Filter articles by recency (configurable max age)
- **🌐 Web Date Scraping** - Extract publication dates from article pages when RSS lacks dates

### 🛠️ Technical Features
- **🔗 Robust URL Handling** - Support for various RSS and Atom feed formats
- **⏱️ Configurable Timeouts** - Per-feed and global timeout controls
- **🔄 Error Recovery** - Graceful handling of failed feeds with fallback options
- **📝 Comprehensive Logging** - Detailed debug information and status tracking
- **🎯 Event Emission** - Real-time status updates during processing
- **📱 Multiple Content Formats** - Support for various RSS/Atom feed structures

## 📋 Requirements

### Required Dependencies
```bash
pip install requests lxml pydantic
```

### Optional Dependencies (Recommended)
```bash
# For async support (highly recommended)
pip install aiohttp asyncio

# For robust date parsing
pip install python-dateutil

# For HTML parsing and date scraping
pip install beautifulsoup4 lxml
```

### Python Version
- **Minimum**: Python 3.7+
- **Recommended**: Python 3.9+

## 🚀 Quick Start

### Basic Usage

```python
from rss_filter import Filter

# Initialize the filter
filter_instance = Filter()

# Configure RSS feeds
filter_instance.valves.rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml,http://rss.cnn.com/rss/cnn_topstories.rss"

# Enable key features
filter_instance.valves.enable_date_scraping = True
filter_instance.valves.enable_concurrent = True
filter_instance.valves.max_articles_per_feed = 10

# Process news request
body = {"messages": [{"content": "What's the latest news?"}]}
result = await filter_instance.inlet(body)
```

## ⚙️ Configuration

### 🔧 Core Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rss_url` | `str` | BBC, CNN, ABC feeds | 📡 Comma-separated RSS feed URLs |
| `enabled` | `bool` | `True` | 🔘 Enable/disable the filter |
| `max_articles_per_feed` | `int` | `7` | 📊 Maximum articles to fetch per feed |
| `max_total_articles_display` | `int` | `10` | 📈 Maximum total articles to display |
| `max_article_age_days` | `int` | `2` | 🗓️ Maximum age of articles in days |

### 🚄 Performance Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_concurrent` | `bool` | `True` | ⚡ Enable async concurrent fetching |
| `max_workers` | `int` | `3` | 👥 Maximum concurrent workers |
| `timeout_seconds` | `int` | `30` | ⏱️ Global operation timeout |
| `per_feed_timeout` | `int` | `15` | ⏰ Individual feed timeout |

### 💾 Caching Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_cache` | `bool` | `True` | 💾 Enable RSS content caching |
| `cache_ttl_seconds` | `int` | `180` | ⏳ Cache time-to-live |
| `cache_stale_if_error` | `bool` | `True` | 🔄 Use stale cache on errors |

### 🕷️ Web Scraping Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_date_scraping` | `bool` | `True` | 🕰️ Scrape dates from article pages |
| `scrape_timeout_seconds` | `int` | `7` | ⏱️ Timeout for page scraping |

### 🎯 Filtering Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_deduplication` | `bool` | `True` | 🔍 Remove duplicate articles |
| `enable_relevance_scoring` | `bool` | `True` | 📊 Score article relevance |
| `min_relevance_score` | `float` | `0.0` | 📉 Minimum relevance threshold |

### 🐛 Debug Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_debug` | `bool` | `True` | 🐛 Show debug messages |
| `show_detailed_status` | `bool` | `True` | 📋 Show detailed status updates |
| `show_links` | `bool` | `True` | 🔗 Include article links |

## 📖 Detailed Usage Examples

### 🔧 Advanced Configuration

```python
from rss_filter import Filter

# Create and configure filter
news_filter = Filter()

# Multi-source configuration
news_filter.valves.rss_url = ",".join([
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "https://abcnews.go.com/abcnews/topstories",
    "https://www.reuters.com/tools/rss",
    "https://feeds.npr.org/1001/rss.xml"
])

# Performance optimization
news_filter.valves.enable_concurrent = True
news_filter.valves.max_workers = 5
news_filter.valves.per_feed_timeout = 10

# Content filtering
news_filter.valves.max_article_age_days = 1  # Only today's news
news_filter.valves.max_total_articles_display = 15
news_filter.valves.article_description_length = 500

# Advanced filtering
news_filter.valves.enable_relevance_scoring = True
news_filter.valves.min_relevance_score = 0.3
news_filter.valves.enable_deduplication = True

# Web scraping for better dates
news_filter.valves.enable_date_scraping = True
news_filter.valves.scrape_timeout_seconds = 5
```

### 🎯 Query Processing

```python
async def process_news_query(user_message, event_emitter=None):
    """Process a news-related query"""
    
    body = {
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    # Process the request
    result = await news_filter.inlet(
        body, 
        __event_emitter__=event_emitter
    )
    
    return result

# Example queries that trigger news fetching
queries = [
    "What's the latest news?",
    "Tell me today's headlines",
    "Any breaking news happening?",
    "Give me current events updates",
    "What's happening in the world?"
]

for query in queries:
    result = await process_news_query(query)
    print(f"Processed: {query}")
```

## 🕰️ Date Extraction System

### 📅 RSS Date Parsing

The filter supports multiple date formats commonly found in RSS feeds:
- RFC 2822: `Mon, 15 Jan 2024 14:30:00 +0000`
- ISO 8601: `2024-01-15T14:30:00Z`
- ISO with timezone: `2024-01-15T14:30:00+00:00`
- And many more variations

### 🕷️ Web Scraping Fallback

When RSS feeds lack publication dates, the system automatically scrapes article pages looking for:

#### 🏷️ Meta Tags
- `<meta property="article:published_time" content="...">`
- `<meta name="pubdate" content="...">`
- `<meta name="date" content="...">`
- `<meta property="og:updated_time" content="...">`

#### 🏷️ HTML Elements
- `<time datetime="...">...</time>`
- Site-specific selectors for major news sources

#### 📊 Structured Data
- JSON-LD structured data with `datePublished`
- Microdata and RDFa date properties

### 🌐 Site-Specific Extractors

Special handling for major news sources:
- **BBC**: `<time data-testid="timestamp">`
- **CNN**: `.timestamp`, `.metadata` selectors
- **ABC News**: `.TimeStamp__Date`, `.xvlfTak` selectors

## 🔍 Filtering & Processing Pipeline

### 1️⃣ **Fetch Phase**
```
📡 RSS Feeds → ⚡ Concurrent/Sync Fetch → 💾 Cache Storage
```

### 2️⃣ **Parse Phase**
```
📰 Raw XML → 🔍 Article Extraction → 🕰️ Date Parsing/Scraping
```

### 3️⃣ **Filter Phase**
```
📅 Age Filter → 🔍 Deduplication → 📊 Relevance Scoring → ✂️ Limit
```

### 4️⃣ **Output Phase**
```
📝 Format Articles → 🔗 Add Links → 📤 Inject into Messages
```

## 🐛 Troubleshooting

### Common Issues

#### 🚫 "No articles found"
**Possible causes:**
- RSS feeds are down or invalid
- All articles are older than `max_article_age_days`
- Network connectivity issues
- Date parsing failures

**Solutions:**
```python
# Increase max age
filter_instance.valves.max_article_age_days = 7

# Enable debug logging
filter_instance.valves.show_debug = True

# Check feed URLs manually
import requests
response = requests.get("YOUR_RSS_URL")
print(response.status_code, response.text[:500])
```

#### ⏱️ Timeout Issues
**Solutions:**
```python
# Increase timeouts
filter_instance.valves.timeout_seconds = 60
filter_instance.valves.per_feed_timeout = 30

# Reduce concurrent workers
filter_instance.valves.max_workers = 2
```

#### 🕰️ Date Scraping Problems
**Check dependencies:**
```bash
pip install beautifulsoup4 lxml
```

**Enable detailed logging:**
```python
filter_instance.valves.show_debug = True
# Check logs for "Scraping date from URL" messages
```

### 📊 Debug Information

Enable comprehensive debugging:
```python
filter_instance.valves.show_debug = True
filter_instance.valves.show_detailed_status = True
```

This will provide detailed logs including:
- RSS fetch attempts and results
- Date parsing attempts and results
- Web scraping operations
- Filtering pipeline statistics
- Cache hit/miss information

## 🧪 Testing

### Unit Tests
```python
import unittest
from rss_filter import Filter

class TestRSSFilter(unittest.TestCase):
    def setUp(self):
        self.filter = Filter()
        
    def test_date_parsing(self):
        """Test various date formats"""
        test_dates = [
            "Mon, 15 Jan 2024 14:30:00 +0000",
            "2024-01-15T14:30:00Z",
            "2024-01-15T14:30:00+00:00"
        ]
        
        for date_str in test_dates:
            parsed = self.filter._parse_datetime(date_str)
            self.assertIsNotNone(parsed)
            
    def test_deduplication(self):
        """Test article deduplication"""
        articles = [
            {"title": "Breaking: Major Event", "link": "http://example.com/1"},
            {"title": "Breaking: Major Event", "link": "http://example.com/1"},  # Duplicate
            {"title": "Different News", "link": "http://example.com/2"}
        ]
        
        result = self.filter._deduplicate_articles(articles)
        self.assertEqual(len(result), 2)

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing
```python
async def test_full_pipeline():
    """Test complete news processing pipeline"""
    filter_instance = Filter()
    
    # Configure test feeds
    filter_instance.valves.rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
    filter_instance.valves.max_articles_per_feed = 3
    
    # Test query
    body = {"messages": [{"content": "latest news"}]}
    
    result = await filter_instance.inlet(body)
    
    # Verify results
    assert len(result["messages"]) > 1  # Should have system message
    assert "RSS FEED ACTIVE" in result["messages"][0]["content"]

# Run test
import asyncio
asyncio.run(test_full_pipeline())
```

## 📈 Performance Optimization

### ⚡ Speed Improvements

1. **Enable Async Processing**
   ```python
   filter_instance.valves.enable_concurrent = True
   filter_instance.valves.max_workers = 5  # Adjust based on your system
   ```

2. **Optimize Caching**
   ```python
   filter_instance.valves.enable_cache = True
   filter_instance.valves.cache_ttl_seconds = 300  # 5 minutes
   ```

3. **Reduce Scraping Overhead**
   ```python
   filter_instance.valves.scrape_timeout_seconds = 5  # Faster timeout
   filter_instance.valves.enable_date_scraping = False  # If not needed
   ```

### 💾 Memory Optimization

```python
# Limit article processing
filter_instance.valves.max_articles_per_feed = 5
filter_instance.valves.max_total_articles_display = 10
filter_instance.valves.article_description_length = 200

# Clean up old cache periodically
def cleanup_cache():
    current_time = time.time()
    expired_keys = [
        key for key, timestamp in filter_instance._cache_timestamps.items()
        if current_time - timestamp > filter_instance.valves.cache_ttl_seconds * 2
    ]
    for key in expired_keys:
        del filter_instance._cache[key]
        del filter_instance._cache_timestamps[key]
```

## 🔌 API Reference

### Main Classes

#### `Filter`
The main filter class that processes RSS feeds.

**Methods:**
- `__init__()`: Initialize the filter
- `inlet(body, __user__, __event_emitter__)`: Process incoming messages
- `outlet(body, __user__, __event_emitter__)`: Process outgoing messages

#### `Filter.Valves`
Configuration class containing all filter settings.

**Key Properties:**
- `rss_url`: Comma-separated RSS feed URLs
- `enabled`: Enable/disable filter
- `max_articles_per_feed`: Articles per feed limit
- `enable_concurrent`: Enable async processing
- `enable_date_scraping`: Enable web date scraping

### Private Methods

#### Date Processing
- `_parse_datetime(date_str)`: Parse date strings
- `_format_date(parsed_dt)`: Format dates for display
- `_get_time_ago(parsed_dt)`: Get relative time strings
- `_scrape_date_from_url(url, domain)`: Extract dates from web pages

#### Content Processing
- `_parse_rss_content(content, source)`: Parse RSS XML
- `_deduplicate_articles(articles)`: Remove duplicates
- `_calculate_relevance_score(article, query_words)`: Score relevance

#### Networking
- `_fetch_feed_async(session, url, idx, total, emitter)`: Async feed fetching
- `_fetch_all_feeds_async(urls, emitter)`: Batch async fetching

#### Caching
- `_get_cached_rss_content(url)`: Retrieve cached content
- `_set_cached_rss_content(url, content)`: Store cached content

## 🤝 Contributing

### 🔧 Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/rss-news-filter.git
   cd rss-news-filter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Run tests**
   ```bash
   python -m pytest tests/
   ```

### 📝 Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for public methods
- Keep functions focused and modular

### 🐛 Bug Reports

When reporting bugs, please include:
- Python version
- Installed dependencies versions
- Full error traceback
- Steps to reproduce
- Expected vs actual behavior

### ✨ Feature Requests

Before submitting feature requests:
- Check existing issues
- Provide clear use case
- Consider backward compatibility
- Offer to help implement if possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **RSS/Atom Standards**: Built on RSS 2.0 and Atom 1.0 specifications
- **BeautifulSoup**: HTML parsing for date extraction
- **aiohttp**: Async HTTP client for concurrent fetching
- **python-dateutil**: Robust date parsing capabilities
- **Pydantic**: Configuration validation and management

## 📞 Support

- 📧 **Email**: support@your-domain.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

<div align="center">

**🌟 Star this repo if you find it helpful! 🌟**

Made with ❤️ for the news aggregation community

</div>
