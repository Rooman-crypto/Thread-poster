
import requests
import re
import html
import datetime

BASE = "https://2ch.org"

def get_threads(board):
    r = requests.get(f"{BASE}/{board}/threads.json", headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    return r.json()

def get_thread(board, thread_id):
    r = requests.get(f"{BASE}/{board}/res/{thread_id}.json", headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    return r.json()

def clean_comment(comment_html):
    # Your existing function
    text = comment_html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return text.strip()

def linkify_replies(text, post_map):
    """Find >>NUMBER references and append Telegram link if that post was sent."""
    def replace(match):
        num_str = match.group(1)
        # post_map keys might be int (in memory) or str (loaded from JSON)
        link = post_map.get(num_str)
        if link is None:
            link = post_map.get(int(num_str))
        
        if link:
            # link is always a list now — take the first Telegram message URL
            return f"{match.group(0)} {link[0]}"
        
        # Not in post_map yet — keep original >>NUMBER
        return match.group(0)
    
    return re.sub(r'>>(\d+)', replace, text)

