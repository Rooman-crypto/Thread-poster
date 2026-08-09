from pathlib import Path
import json
import os


STATE_FILE = Path(__file__).parent / "data" / "bot_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = Path(__file__).parent / "config.py"


def load_state():
    if not os.path.exists(STATE_FILE):
        return set(), {}, {}, None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("Warning: state file corrupted, starting fresh.")
        return set(), {}, {}, None

    seen_posts = set(data.get("seen_posts", []))
    post_map = data.get("post_map", {})
    message_data = data.get("message_data", {})
    saved_start = data.get("start_post", None)

    return seen_posts, post_map, message_data, saved_start


def save_state(seen_posts, post_map, message_data, start_post):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seen_posts": list(seen_posts),
                "post_map": post_map,
                "message_data": message_data,
                "start_post": start_post,
            },
            f,
            ensure_ascii=False,
            indent=4,
        )


def clear_thread_state(start_post=1):
    """Clear all tracked data when switching to a new thread."""
    save_state(set(), {}, {}, start_post)


def update_config_thread_id(new_thread_id):
    """Persist the new thread ID into config.py."""
    if not CONFIG_PATH.exists():
        print("Warning: config.py not found, cannot persist thread ID.")
        return

    text = CONFIG_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        if (
            stripped.startswith("THREAD_ID")
            and "=" in stripped
            and not stripped.startswith("#")
        ):
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f'{indent}THREAD_ID = "{new_thread_id}"'
            break
    else:
        print("Warning: THREAD_ID assignment not found in config.py")
        return

    CONFIG_PATH.write_text(
        "\n".join(lines) + ("\n" if text.endswith("\n") else ""),
        encoding="utf-8",
    )


def remember_post(post, message_data, published):
    message_data[str(post["num"])] = {
        "tg_message_id": published.message_id,
        "text": published.text,
        "type": published.message_type,
        "files": post.get("files") or [],
        "number": post["number"],
    }


def remember_links(post_map, post_num, all_links):
    if post_num in post_map:
        post_map[post_num].extend(all_links)
    else:
        post_map[post_num] = all_links


def update_replied_message(message_data, reply, text):
    message_data[reply]["text"] = text
