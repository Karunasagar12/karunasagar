#!/usr/bin/env python3
"""
DHA Medical Directory Scraper - CloudScraper Version
Alternative approach using cloudscraper library for Cloudflare bypass

Install: pip install cloudscraper beautifulsoup4 lxml
"""

import argparse
import json
import random
import time
from datetime import datetime

try:
    import cloudscraper
except ImportError:
    print("Install cloudscraper: pip install cloudscraper")
    exit(1)

from bs4 import BeautifulSoup
import csv
import re
import os


class DHAScraper:
    def __init__(self, proxy=None):
        self.results = []
        self.proxy = proxy
        self.scraper = None

    def create_scraper(self):
        """Create cloudscraper instance"""
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )
        if self.proxy:
            self.scraper.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
        print(f"Created scraper (proxy: {'Yes' if self.proxy else 'No'})")

    def scrape_page(self, url, retry_count=0):
        """Scrape a single page"""
        max_retries = 3
        dha_id = url.split('dhaUniqueId=')[-1]

        try:
            time.sleep(random.uniform(3, 6))

            response = self.scraper.get(url, timeout=30)

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            content = response.text

            if len(content) < 500 and 'access denied' in content.lower():
                raise Exception("Access denied")

            soup = BeautifulSoup(content, 'lxml')

            data = {
                'dha_unique_id': dha_id,
                'url': url,
                'scraped_at': datetime.now().isoformat()
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

            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            structured_data[key] = value

            for dl in soup.find_all('dl'):
                for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
                    key = dt.get_text(strip=True)
                    value = dd.get_text(strip=True)
                    if key and value:
                        structured_data[key] = value

            if structured_data:
                data['structured_data'] = structured_data

            # Save HTML
            os.makedirs('/home/user/karunasagar/html', exist_ok=True)
            with open(f'/home/user/karunasagar/html/page_{dha_id}.html', 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✓ {dha_id}: {response.status_code}")
            return data

        except Exception as e:
            print(f"✗ {dha_id}: {e}")
            if retry_count < max_retries:
                print(f"  Retry {retry_count + 1}...")
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
        self.create_scraper()

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
        """Save results"""
        with open('/home/user/karunasagar/scrape_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        if self.results:
            flat = []
            for r in self.results:
                item = {
                    'dha_unique_id': r.get('dha_unique_id', ''),
                    'url': r.get('url', ''),
                    'page_title': r.get('page_title', ''),
                    'scraped_at': r.get('scraped_at', ''),
                    'error': r.get('error', '')
                }
                if 'structured_data' in r:
                    for k, v in r['structured_data'].items():
                        item[re.sub(r'[^\w\s]', '', k).strip()[:50]] = v
                flat.append(item)

            keys = set()
            for i in flat:
                keys.update(i.keys())

            with open('/home/user/karunasagar/scrape_results.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(keys))
                writer.writeheader()
                writer.writerows(flat)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxy', help='Proxy URL')
    args = parser.parse_args()

    urls = [
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=31701021",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=95753410",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=49452352",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=51274983",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=77227808",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=40212780",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=99987711",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=26397118",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=52784111",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=94140481",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=15873015",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=64123001",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=28181178",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=49809921",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=72034974",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=10924746",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=77038398",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=66841992",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=77923690",
        "https://services.dha.gov.ae/sheryan/wps/portal/home/medical-directory/professional-details?dhaUniqueId=97411409",
    ]

    print("=" * 50)
    print("DHA Scraper (CloudScraper)")
    print(f"URLs: {len(urls)}")
    print("=" * 50)

    scraper = DHAScraper(proxy=args.proxy)
    results = scraper.scrape_urls(urls)

    print("\n" + "=" * 50)
    success = len([r for r in results if 'error' not in r])
    print(f"Success: {success} | Failed: {len(results) - success}")
    print("=" * 50)


if __name__ == "__main__":
    main()
