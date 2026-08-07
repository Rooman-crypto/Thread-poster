import json
import os

STATE_FILE = "bot_state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return set(), {}, {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("Warning: state file corrupted, starting fresh.")
        return set(), {}, {}

    seen_posts = set(data.get("seen_posts", []))
    post_map = data.get("post_map", {})
    message_data = data.get("message_data", {})

    return seen_posts, post_map, message_data


def save_state(seen_posts, post_map, message_data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seen_posts": list(seen_posts),
                "post_map": post_map,
                "message_data": message_data,
            },
            f,
            ensure_ascii=False,
            indent=4,
        )