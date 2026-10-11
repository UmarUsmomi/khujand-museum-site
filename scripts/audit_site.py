import glob
import os
import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

html_files = ['index.html'] + sorted(glob.glob('pages/*.html'))

for path in html_files:
    print(f"\n==================== {path} ====================")
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Title & Description
    title = soup.title.string.strip() if soup.title and soup.title.string else 'NONE'
    desc_tag = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else 'NONE'
    canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
    canonical = canonical_tag['href'].strip() if canonical_tag and canonical_tag.get('href') else 'NONE'
    robots_tag = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
    robots = robots_tag['content'].strip() if robots_tag and robots_tag.get('content') else 'NONE'
    
    print(f"Title: {title}")
    print(f"Description: {desc}")
    print(f"Canonical: {canonical}")
    print(f"Robots: {robots}")
    
    # H1
    h1_list = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
    print(f"H1 ({len(h1_list)}): {h1_list}")
    
    # Preconnects & stylesheets
    links = soup.find_all('link')
    for l in links:
        rel = l.get('rel', [])
        if isinstance(rel, list):
            rel = ' '.join(rel)
        if 'stylesheet' in rel or 'preconnect' in rel or 'preload' in rel:
            print(f"  Link: rel={rel} href={l.get('href')}")
            
    # Scripts
    scripts = soup.find_all('script', src=True)
    for s in scripts:
        defer = 'defer' in s.attrs
        async_attr = 'async' in s.attrs
        print(f"  Script: src={s['src']} defer={defer} async={async_attr}")
        
    # Videos
    videos = soup.find_all('video')
    for v in videos:
        print(f"  Video: src={v.get('src')} preload={v.get('preload')} poster={v.get('poster')}")
