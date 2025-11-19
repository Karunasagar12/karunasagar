# DHA Medical Directory Scraper

Scrapes medical professional details from the DHA Sheryan portal.

## Important Note

The DHA website blocks requests from cloud/datacenter IP addresses. You need to either:
1. **Run locally** on your home/residential network
2. **Use a residential proxy** service

## Installation

```bash
pip install -r requirements.txt
```

## Available Scrapers

### 1. dha_scraper_final.py (Recommended)
Uses curl-cffi with browser impersonation - best for bypassing TLS fingerprinting.

```bash
# Run locally (residential IP)
python dha_scraper_final.py

# With single proxy
python dha_scraper_final.py --proxy "http://user:pass@proxy:port"

# With rotating proxies
python dha_scraper_final.py --proxy-file proxies.txt
```

### 2. dha_scraper_cloudscraper.py
Uses cloudscraper library - good for Cloudflare bypass.

```bash
python dha_scraper_cloudscraper.py
python dha_scraper_cloudscraper.py --proxy "http://user:pass@proxy:port"
```

## Proxy Providers

For residential proxies, consider:
- Bright Data (formerly Luminati)
- Oxylabs
- Smartproxy
- IPRoyal

## Output

Results are saved to:
- `scrape_results.json` - Full data with all extracted content
- `scrape_results.csv` - Flattened data for spreadsheet analysis
- `html/` - Raw HTML files for each page

## Customization

To scrape different URLs, edit the `urls` list in the main() function of the scraper file.

## Rate Limiting

The scrapers include random delays (6-12 seconds) between requests to avoid detection. Increase delays if you encounter blocking.

## Troubleshooting

**403 Access Denied**:
- You're likely on a blocked IP (cloud/VPN/datacenter)
- Use a residential proxy or run from your home network

**429 Too Many Requests**:
- Increase delays between requests
- Reduce concurrent scraping
- Use rotating proxies

**Empty or incomplete data**:
- Check the saved HTML files in the `html/` directory
- The page structure may have changed - update selectors accordingly
