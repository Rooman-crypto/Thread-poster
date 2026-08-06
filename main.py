
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

# --- Usage ---
board = 'fag'
thread_id = 27574729

data = get_thread(board, thread_id)
posts = data['threads'][0]['posts']

#for i, post in enumerate(posts):
#    comment = clean_comment(post.get('comment', ''))
#    timestamp = datetime.datetime.fromtimestamp(int(post['timestamp'])
#                                       ).strftime('%Y-%m-%d %H:%M:%S')
#    print(f"{timestamp} | #{post['num']} | {post.get('number')}")
#    print(f"{comment}")
#    print()
#    if post.get('files'):
#        for f in post['files']:
#            print(f"📎 https://2ch.org{f['path']}")#for post in range(thread['posts_count']):
#    print()
