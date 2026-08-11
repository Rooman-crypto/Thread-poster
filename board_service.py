import requests
import re
import html
import datetime


BASE = "https://2ch.org"


def get_threads(board):
    r = requests.get(
        f"{BASE}/{board}/threads.json",
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    r.raise_for_status()

    return r.json()


def get_thread(board, thread_id):
    r = requests.get(
        f"{BASE}/{board}/res/{thread_id}.json",
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    r.raise_for_status()

    return r.json()


def clean_comment(comment_html):
    text = (
        comment_html
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )

    text = re.sub(
        r"<a[^>]*>(.*?)</a>",
        r"\1",
        text,
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = html.unescape(text)

    return text.strip()

def linkify_replies(text, post_map):
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

            return f"№{num_str}\n{link[0]}\n"

        return match.group(0)

    new_text = re.sub(
        r">>(\d+)",
        replace,
        text,
    )

    return (
        new_text,
        list(dict.fromkeys(linked_nums)),
    )
def extract_new_thread_candidates(
    comment_text,
    current_thread_id,
):
    """
    Find >>NUMBER (OP) references that could indicate
    a switch to another thread.

    The current thread ID is ignored.
    Duplicate candidates are removed.
    """

    if not comment_text:
        return []

    current = str(current_thread_id)

    nums = re.findall(
        r">\s*>\s*(\d+)\s*\(OP\)",
        comment_text,
    )

    candidates = []
    seen = set()

    for num in nums:
        if num == current:
            continue

        if num not in seen:
            seen.add(num)
            candidates.append(num)

    return candidates
