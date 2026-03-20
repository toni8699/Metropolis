import requests
import re

def fetch_and_print_grid(google_doc_url: str) -> None:
    response = requests.get(google_doc_url)
    response.raise_for_status()
    text = response.text

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', text, re.DOTALL)
    
    grid = {}
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(cells) == 3:
            try:
                x, char, y = int(cells[0]), cells[1], int(cells[2])
                grid[(x, y)] = char
            except ValueError:
                continue

    if not grid:
        print("No grid data found.")
        return

    max_x = max(x for x, y in grid)
    max_y = max(y for x, y in grid)

    for y in range(max_y, -1, -1):
        print("".join(grid.get((x, y), " ") for x in range(max_x + 1)))


fetch_and_print_grid("https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub")