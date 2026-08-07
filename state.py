from pathlib import Path
import json
import os

STATE_FILE = Path(__file__).parent / "data" / "bot_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)



def load_state():
    if not os.path.exists(STATE_FILE):
        return set(), {}, {}, 0  # ← was missing , 0

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("Warning: state file corrupted, starting fresh.")
        return set(), {}, {}, 0  # ← was missing , 0

    seen_posts = set(data.get("seen_posts", []))
    post_map = data.get("post_map", {})
    message_data = data.get("message_data", {})
    saved_start = data.get('start_post', 0)

    return seen_posts, post_map, message_data, saved_start

def save_state(seen_posts, post_map, message_data,start_post):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seen_posts": list(seen_posts),
                "post_map": post_map,
                "message_data": message_data,
                "start_post":start_post,
            },
            f,
            ensure_ascii=False,
            indent=4,
        )
def remember_post(post,message_sent,message_data,text,message_id,msg_type):
    message_data[str(post.get('num'))] = {
    "tg_message_id": message_id ,
    "text": text,
    "type": msg_type,
    "files": post['files'],
    "number": post['number']
    }
    
def remember_links(post_map,post,all_links):
    post_map[post.get('num')] = all_links

def update_replied_message(message_data,post):
    pass
