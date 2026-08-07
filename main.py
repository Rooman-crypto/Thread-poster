
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
    """Find >>NUMBER references and append Telegram link if that post was sent.
    
    Returns:
        (new_text, was_modified, linked_nums)
        linked_nums is a list of post numbers (as strings) that were found in post_map
    """
    was_modified = False
    linked_nums = []
    
    def replace(match):
        nonlocal was_modified
        num_str = match.group(1)
        
        link = post_map.get(num_str)
        if link is None:
            link = post_map.get(int(num_str))
        
        if link:
            was_modified = True
            linked_nums.append(num_str)
            return f"{match.group(0)} {link[0]}"
        
        return match.group(0)
    
    new_text = re.sub(r'>>(\d+)', replace, text)
    return new_text, was_modified, list(dict.fromkeys(linked_nums))

