"""
Regenerates the ASCII contribution graph in README.md from public
GitHub contribution data. Run manually or via the scheduled workflow.
"""
import re
import urllib.request
from collections import defaultdict
from datetime import datetime

USERNAME = "altschrei"
README_PATH = "README.md"
START_MARKER = "<!--START_SECTION:activity-->"
END_MARKER = "<!--END_SECTION:activity-->"


def fetch_contributions_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def build_ascii_graph(html: str) -> str:
    total_match = re.search(r"<h2[^>]*>\s*(\d+)\s*\n\s*contributions", html)
    total = total_match.group(1) if total_match else "?"

    pattern = re.compile(
        r'data-date="([\d-]+)" id="contribution-day-component-(\d+)-(\d+)" '
        r'data-level="(\d)"'
    )
    cells = pattern.findall(html)

    grid = defaultdict(dict)
    dates = {}
    for date, dow, week, level in cells:
        dow, week, level = int(dow), int(week), int(level)
        grid[week][dow] = level
        dates[(week, dow)] = date

    if not grid:
        return "no contribution data available"

    max_week = max(grid.keys())
    chars = {0: "·", 1: "-", 2: "o", 3: "O", 4: "#"}

    month_row = [" "] * (max_week + 1)
    last_month = None
    for week in range(max_week + 1):
        date_str = dates.get((week, 0)) or dates.get((week, 1))
        if date_str:
            m = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b")
            if m != last_month:
                for i, ch in enumerate(m):
                    if week + i <= max_week:
                        month_row[week + i] = ch
                last_month = m

    lines = ["    " + "".join(month_row)]
    dow_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for dow in range(7):
        row = [chars[grid.get(week, {}).get(dow, 0)] for week in range(max_week + 1)]
        label = dow_labels.get(dow, "   ")
        lines.append(f"{label} " + "".join(row))

    art = "\n".join(lines)
    return f"```\n{art}\n\n               {total} contributions in the last year\n```"


def update_readme(new_block: str) -> bool:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )
    replacement = f"{START_MARKER}\n{new_block}\n{END_MARKER}"
    new_content, count = pattern.subn(replacement, content)

    if count == 0:
        raise RuntimeError("Markers not found in README.md")

    if new_content == content:
        return False

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


if __name__ == "__main__":
    html = fetch_contributions_html(USERNAME)
    graph = build_ascii_graph(html)
    changed = update_readme(graph)
    print("README updated" if changed else "No changes")
