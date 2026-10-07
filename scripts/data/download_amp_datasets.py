import os
import sys
import re
import json
import time
import urllib.request
import http.cookiejar
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://www.datosabiertos.gob.pa"
ORG_URL = f"{BASE_URL}/dataset/?organization=autoridad-maritima-de-panama-amp"
OUTPUT_DIR = os.path.join(os.getcwd(), "data", "raw")
METADATA_DIR = os.path.join(os.getcwd(), "data", "metadata")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def create_opener():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', USER_AGENT),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'es-ES,es;q=0.9,en;q=0.8')
    ]
    return opener

opener = create_opener()

def sanitize_filename(name):
    # Remove accents/diacritics or simplify
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '_', name.strip())
    return name[:120]

def fetch_page_datasets(page_num, retries=3):
    url = f"{ORG_URL}&page={page_num}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('.table-card')
            results = []
            for card in cards:
                title_el = card.select_one('.dataset-title a')
                title = title_el.get_text(strip=True) if title_el else ""
                href = title_el['href'] if title_el and 'href' in title_el.attrs else ""
                desc_el = card.select_one('.description')
                desc = desc_el.get_text(strip=True) if desc_el else ""
                
                # Check format badges on card
                badges = [img.get('alt', '').upper() for img in card.select('.card-dap-1--files img')]
                
                results.append({
                    'page': page_num,
                    'title': title,
                    'dataset_url': BASE_URL + href if href.startswith('/') else href,
                    'slug': href.strip('/').split('/')[-1] if href else "",
                    'description': desc,
                    'card_formats': badges
                })
            return results
        except Exception as e:
            time.sleep(1 + attempt)
            if attempt == retries - 1:
                print(f"Error fetching page {page_num}: {e}")
                return []

def get_dataset_resources(dataset_info, retries=3):
    slug = dataset_info['slug']
    # Use CKAN API package_show for robust resource extraction
    api_url = f"{BASE_URL}/api/3/action/package_show?id={slug}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='replace'))
            if data.get('success'):
                pkg = data['result']
                resources = pkg.get('resources', [])
                csv_res = next((r for r in resources if (r.get('format') or '').upper() == 'CSV'), None)
                excel_res = next((r for r in resources if (r.get('format') or '').upper() in ['XLSX', 'XLS']), None)
                return {
                    'pkg_metadata': {
                        'id': pkg.get('id'),
                        'metadata_created': pkg.get('metadata_created'),
                        'metadata_modified': pkg.get('metadata_modified'),
                        'notes': pkg.get('notes'),
                        'tags': [t.get('name') for t in pkg.get('tags', [])]
                    },
                    'csv_url': csv_res.get('url') if csv_res else None,
                    'csv_name': csv_res.get('name') if csv_res else None,
                    'excel_url': excel_res.get('url') if excel_res else None,
                    'excel_name': excel_res.get('name') if excel_res else None
                }
        except Exception as e:
            time.sleep(0.5 + attempt)
            if attempt == retries - 1:
                pass
    
    # Fallback to scraping the dataset page directly
    try:
        req = urllib.request.Request(dataset_info['dataset_url'], headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')
        csv_url = None
        excel_url = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '.csv' in href.lower():
                csv_url = href
            elif any(ext in href.lower() for ext in ['.xlsx', '.xls']):
                excel_url = href
        return {
            'pkg_metadata': {},
            'csv_url': csv_url,
            'csv_name': None,
            'excel_url': excel_url,
            'excel_name': None
        }
    except Exception as e:
        print(f"Fallback page parse error for {slug}: {e}")
        return {'pkg_metadata': {}, 'csv_url': None, 'excel_url': None}

def download_file(url, target_path, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=25) as resp:
                content = resp.read()
            with open(target_path, 'wb') as f:
                f.write(content)
            return len(content)
        except Exception as e:
            time.sleep(1 + attempt)
            if attempt == retries - 1:
                print(f"Failed to download {url}: {e}")
                return None

def process_single_dataset(item, index, total):
    res = get_dataset_resources(item)
    slug = item['slug']
    title = item['title']
    
    target_url = None
    target_format = None
    if res.get('csv_url'):
        target_url = res['csv_url']
        target_format = 'CSV'
    elif res.get('excel_url'):
        target_url = res['excel_url']
        target_format = 'EXCEL'
    
    status = 'MISSING_RESOURCE'
    local_file = None
    file_size = 0
    
    if target_url:
        ext = '.csv' if target_format == 'CSV' else ('.xlsx' if '.xlsx' in target_url.lower() else '.xls')
        clean_title = sanitize_filename(slug if slug else title)
        filename = f"{clean_title}{ext}"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Download
        size = download_file(target_url, filepath)
        if size is not None and size > 0:
            status = 'DOWNLOADED'
            local_file = filename
            file_size = size
        else:
            # If CSV failed, try Excel fallback!
            if target_format == 'CSV' and res.get('excel_url'):
                excel_url = res['excel_url']
                ext = '.xlsx' if '.xlsx' in excel_url.lower() else '.xls'
                filename = f"{clean_title}{ext}"
                filepath = os.path.join(OUTPUT_DIR, filename)
                size = download_file(excel_url, filepath)
                if size is not None and size > 0:
                    status = 'DOWNLOADED_FALLBACK_EXCEL'
                    local_file = filename
                    file_size = size
                    target_format = 'EXCEL'
                    target_url = excel_url
                else:
                    status = 'FAILED_DOWNLOAD'
            else:
                status = 'FAILED_DOWNLOAD'
                
    result_record = {
        'index': index,
        'page': item['page'],
        'slug': slug,
        'title': title,
        'description': item['description'],
        'dataset_url': item['dataset_url'],
        'format_selected': target_format,
        'download_url': target_url,
        'status': status,
        'local_file': local_file,
        'file_size_bytes': file_size,
        'csv_url': res.get('csv_url'),
        'excel_url': res.get('excel_url'),
        'metadata': res.get('pkg_metadata', {})
    }
    
    if (index + 1) % 25 == 0 or index == total - 1:
        print(f"[{index+1}/{total}] Processed: {title[:50]}... -> {status} ({file_size} bytes)")
        
    return result_record

def main():
    print("=== Step 1: Discovering all pages and datasets ===")
    all_datasets = []
    page = 1
    while True:
        datasets = fetch_page_datasets(page)
        if not datasets:
            print(f"Page {page} returned 0 datasets. Finished pagination.")
            break
        print(f"Page {page}: found {len(datasets)} datasets.")
        all_datasets.extend(datasets)
        page += 1
        time.sleep(0.3)
        
    total = len(all_datasets)
    print(f"\nTotal datasets discovered across all {page-1} pages: {total}")
    
    print("\n=== Step 2: Downloading datasets (CSV preferred, Excel fallback) ===")
    records = []
    
    # Use ThreadPoolExecutor with 5 workers for respectful yet fast downloads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_single_dataset, item, idx, total): idx for idx, item in enumerate(all_datasets)}
        for future in as_completed(futures):
            records.append(future.result())
            
    records.sort(key=lambda r: r['index'])
    
    # Save metadata catalog
    catalog_json_path = os.path.join(METADATA_DIR, "datasets_catalog.json")
    with open(catalog_json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    df_catalog = pd.DataFrame([{
        'index': r['index'],
        'page': r['page'],
        'slug': r['slug'],
        'title': r['title'],
        'status': r['status'],
        'format': r['format_selected'],
        'file_size_kb': round(r['file_size_bytes'] / 1024, 2),
        'local_file': r['local_file'],
        'download_url': r['download_url'],
        'description': r['description']
    } for r in records])
    
    catalog_csv_path = os.path.join(METADATA_DIR, "datasets_catalog.csv")
    df_catalog.to_csv(catalog_csv_path, index=False, encoding="utf-8-sig")
    
    print("\n=== Step 3: Summary of Downloads ===")
    print(df_catalog['status'].value_counts())
    print(f"\nTotal files downloaded in {OUTPUT_DIR}: {len(os.listdir(OUTPUT_DIR))}")
    print(f"Catalog saved to {catalog_csv_path} and {catalog_json_path}")

if __name__ == "__main__":
    main()
