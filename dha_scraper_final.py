#!/usr/bin/env python3
"""
DHA Medical Directory Scraper - Final Version
Includes proxy support and multiple bypass techniques

USAGE:
    # With Excel file containing URLs:
    python dha_scraper_final.py --excel urls.xlsx

    # Specify column name (default: 'url' or first column):
    python dha_scraper_final.py --excel urls.xlsx --column "Link"

    # With proxy:
    python dha_scraper_final.py --excel urls.xlsx --proxy "http://user:pass@proxy:port"

    # With rotating proxies file:
    python dha_scraper_final.py --excel urls.xlsx --proxy-file proxies.txt
"""

import pandas as pd

import argparse
import json
import random
import time
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup
import csv
import re
import os


class DHAScraper:
    def __init__(self, proxy=None, proxy_list=None):
        self.results = []
        self.session = None
        self.impersonate = None
        self.proxy = proxy
        self.proxy_list = proxy_list
        self.impersonations = [
            'chrome120', 'chrome119', 'chrome116',
            'edge101', 'safari17_0', 'safari15_5'
        ]

    def get_proxy(self):
        """Get a proxy - either single or from rotating list"""
        if self.proxy_list:
            return random.choice(self.proxy_list)
        return self.proxy

    def create_session(self):
        """Create session with browser impersonation and optional proxy"""
        self.impersonate = random.choice(self.impersonations)
        self.session = requests.Session(impersonate=self.impersonate)
        print(f"Session: browser={self.impersonate}")
        return self.session

    def get_headers(self, referer=None):
        """Get realistic browser headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        if referer:
            headers['Referer'] = referer
        return headers

    def establish_session(self):
        """Visit base pages to establish cookies"""
        base_url = "https://services.dha.gov.ae/sheryan/wps/portal/home"
        directory_url = "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory"

        proxy = self.get_proxy()
        proxies = {'http': proxy, 'https': proxy} if proxy else None

        try:
            print("Establishing session...")

            # Visit home page
            response = self.session.get(
                base_url,
                headers=self.get_headers(),
                proxies=proxies,
                timeout=30
            )
            print(f"  Home: {response.status_code}")

            if response.status_code == 403:
                print("  Warning: Blocked at home page")
                return False

            time.sleep(random.uniform(2, 4))

            # Visit directory
            response = self.session.get(
                directory_url,
                headers=self.get_headers(base_url),
                proxies=proxies,
                timeout=30
            )
            print(f"  Directory: {response.status_code}")
            time.sleep(random.uniform(2, 4))

            print(f"  Cookies: {len(self.session.cookies)}")
            return response.status_code == 200

        except Exception as e:
            print(f"  Error establishing session: {e}")
            return False

    def scrape_page(self, url, retry_count=0):
        """Scrape a single professional details page"""
        max_retries = 3
        dha_id = url.split('dhaUniqueId=')[-1]

        try:
            time.sleep(random.uniform(3, 6))

            proxy = self.get_proxy()
            proxies = {'http': proxy, 'https': proxy} if proxy else None

            referer = "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory"
            response = self.session.get(
                url,
                headers=self.get_headers(referer),
                proxies=proxies,
                timeout=30,
                allow_redirects=True
            )

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            content = response.text

            if len(content) < 500 and ('access denied' in content.lower() or 'blocked' in content.lower()):
                raise Exception("Access denied")

            soup = BeautifulSoup(content, 'lxml')

            data = {
                'dha_unique_id': dha_id,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'browser': self.impersonate
            }

            # Extract title
            title = soup.find('title')
            if title:
                data['page_title'] = title.get_text(strip=True)

            # Extract headers
            for i, h in enumerate(soup.find_all(['h1', 'h2', 'h3'])):
                text = h.get_text(strip=True)
                if text and len(text) < 200:
                    data[f'header_{i}'] = text

            # Extract structured data
            structured_data = {}

            # From tables
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            structured_data[key] = value

            # From dl
            for dl in soup.find_all('dl'):
                dts = dl.find_all('dt')
                dds = dl.find_all('dd')
                for dt, dd in zip(dts, dds):
                    key = dt.get_text(strip=True)
                    value = dd.get_text(strip=True)
                    if key and value:
                        structured_data[key] = value

            # From div patterns
            for div in soup.find_all('div', class_=re.compile(r'(field|row|item|detail|info)', re.I)):
                label = div.find(class_=re.compile(r'label|key|title', re.I))
                value = div.find(class_=re.compile(r'value|data|content', re.I))
                if label and value:
                    k = label.get_text(strip=True)
                    v = value.get_text(strip=True)
                    if k and v:
                        structured_data[k] = v

            if structured_data:
                data['structured_data'] = structured_data

            # Extract content
            all_text = []
            for elem in soup.find_all(['p', 'span', 'div', 'td', 'li']):
                text = elem.get_text(strip=True)
                if text and 20 < len(text) < 300 and text not in all_text:
                    all_text.append(text)
            data['page_content'] = list(set(all_text))[:50]

            # Save HTML
            html_dir = 'html'
            os.makedirs(html_dir, exist_ok=True)
            html_path = f"{html_dir}/page_{dha_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            data['html_file'] = html_path

            print(f"✓ {dha_id}: {response.status_code} ({len(content)} bytes)")
            return data

        except Exception as e:
            print(f"✗ {dha_id}: {e}")
            if retry_count < max_retries:
                print(f"  Retry {retry_count + 1}/{max_retries}...")
                if retry_count == 1:
                    self.create_session()
                    self.establish_session()
                time.sleep(random.uniform(8, 15))
                return self.scrape_page(url, retry_count + 1)
            return {
                'dha_unique_id': dha_id,
                'url': url,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }

    def scrape_urls(self, urls):
        """Scrape multiple URLs"""
        self.create_session()
        self.establish_session()

        for i, url in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}]")
            result = self.scrape_page(url)
            self.results.append(result)
            self.save_results()

            if i < len(urls) - 1:
                delay = random.uniform(6, 12)
                print(f"  Wait {delay:.1f}s...")
                time.sleep(delay)

        return self.results

    def save_results(self):
        """Save results to JSON and CSV"""
        with open('scrape_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        if self.results:
            flat_results = []
            for result in self.results:
                flat = {
                    'dha_unique_id': result.get('dha_unique_id', ''),
                    'url': result.get('url', ''),
                    'page_title': result.get('page_title', ''),
                    'scraped_at': result.get('scraped_at', ''),
                    'error': result.get('error', '')
                }
                for key, value in result.items():
                    if key.startswith('header_'):
                        flat[key] = value
                if 'structured_data' in result:
                    for key, value in result['structured_data'].items():
                        clean_key = re.sub(r'[^\w\s]', '', key).strip()[:50]
                        if clean_key:
                            flat[clean_key] = value
                flat_results.append(flat)

            all_keys = set()
            for r in flat_results:
                all_keys.update(r.keys())

            priority = ['dha_unique_id', 'url', 'page_title', 'scraped_at', 'error']
            ordered = priority + sorted([k for k in all_keys if k not in priority])

            with open('scrape_results.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=ordered)
                writer.writeheader()
                writer.writerows(flat_results)


def load_urls_from_file(file_path, column=None):
    """Load URLs from an Excel or CSV file"""
    try:
        # Detect file type
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            print(f"Loaded CSV: {len(df)} rows, columns: {list(df.columns)}")
        else:
            df = pd.read_excel(file_path)
            print(f"Loaded Excel: {len(df)} rows, columns: {list(df.columns)}")

        # Find the URL column
        if column and column in df.columns:
            url_column = column
        elif 'url' in df.columns:
            url_column = 'url'
        elif 'URL' in df.columns:
            url_column = 'URL'
        elif 'link' in df.columns:
            url_column = 'link'
        elif 'Link' in df.columns:
            url_column = 'Link'
        else:
            # Use first column
            url_column = df.columns[0]
            print(f"Using first column: '{url_column}'")

        # Extract URLs
        urls = df[url_column].dropna().astype(str).tolist()
        # Filter valid URLs
        urls = [url.strip() for url in urls if url.strip().startswith('http')]

        print(f"Found {len(urls)} URLs in column '{url_column}'")
        return urls

    except Exception as e:
        print(f"Error loading Excel: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='DHA Medical Directory Scraper')
    parser.add_argument('--file', help='Excel (.xlsx) or CSV (.csv) file with URLs')
    parser.add_argument('--column', help='Column name containing URLs (default: auto-detect)')
    parser.add_argument('--proxy', help='Proxy URL (http://user:pass@host:port)')
    parser.add_argument('--proxy-file', help='File with proxy list (one per line)')
    args = parser.parse_args()

    proxy = args.proxy
    proxy_list = None

    if args.proxy_file:
        with open(args.proxy_file) as f:
            proxy_list = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(proxy_list)} proxies")

    # Load URLs from file
    if args.file:
        urls = load_urls_from_file(args.file, args.column)
        if not urls:
            print("No URLs found in file!")
            return
    else:
        print("No input file provided. Use --file urls.csv or --file urls.xlsx")
        print("Example: python dha_scraper_final.py --file Test.csv")
        return

    print("=" * 60)
    print("DHA Medical Directory Scraper")
    print("=" * 60)
    print(f"URLs: {len(urls)}")
    print(f"Proxy: {'Yes' if proxy or proxy_list else 'No'}")
    print("=" * 60)

    scraper = DHAScraper(proxy=proxy, proxy_list=proxy_list)
    results = scraper.scrape_urls(urls)

    print("\n" + "=" * 60)
    print("Complete!")
    success = len([r for r in results if 'error' not in r])
    failed = len([r for r in results if 'error' in r])
    print(f"Success: {success} | Failed: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
