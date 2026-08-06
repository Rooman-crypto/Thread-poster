import json
import os

STATE_FILE = "bot_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f).get('seen_posts', []))
    return set()

def save_state(seen_posts):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'seen_posts': list(seen_posts)}, f)

def load_post_map():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("messages",{})

def save_post_map(messages):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"messages": messages}, f)