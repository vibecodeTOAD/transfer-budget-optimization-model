import re
import time
import pandas as pd
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

LEAGUE_PAYROLLS_URL = "https://www.capology.com/uk/premier-league/payrolls/"

WANTED_COLS = [
    "PLAYER",
    "BASE GROSS P/W (EUR)",
    "BASE GROSS P/Y (EUR)",
    "BONUS GROSS P/Y (EUR)",
    "TOTAL GROSS P/Y (EUR)",
    "SIGNED",
    "EXPIRATION",
    "YEARS REMAINING",
    "GROSS REMAINING (EUR)",
    "RELEASE CLAUSE (EUR)",
]

def norm(s) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"\s+", " ", s.strip()).upper()

def club_links_from_league_page(page) -> list[str]:
    # Grab club links only from the main payrolls table
    # This avoids menu/footer duplicates.
    hrefs = page.eval_on_selector_all(
        "table a[href^='/club/']",
        "els => els.map(e => e.getAttribute('href'))"
    )

    clubs = []
    for h in hrefs:
        if not h:
            continue
        full = urljoin("https://www.capology.com", h)

        # normalize to base club URL: https://www.capology.com/club/<slug>
        m = re.search(r"(https://www\.capology\.com/club/[^/]+)", full)
        if m:
            clubs.append(m.group(1))

    # de-dupe in order
    seen, out = set(), []
    for u in clubs:
        if u not in seen:
            seen.add(u)
            out.append(u)

    return out

def to_salaries_url(club_base_url: str) -> str:
    return club_base_url.rstrip("/") + "/salaries/"

def click_if_exists(page, text: str):
    loc = page.locator(f"button:has-text('{text}')")
    if loc.count() > 0:
        loc.first.click()
        page.wait_for_timeout(800)

def extract_contracts_table(page):
    # Try to target the Contracts table specifically by finding the header "Contracts"
    # then the next table on the page.
    table = None

    # If there are multiple tables, choose the one that contains "PLAYER" in header
    tables = page.locator("table")
    for i in range(tables.count()):
        t = tables.nth(i)
        headers = [norm(x) for x in t.locator("thead th").all_inner_texts()]
        if any("PLAYER" == h or "PLAYER" in h for h in headers):
            table = t
            break

    if table is None:
        return [], []

    headers = [re.sub(r"\s+", " ", x).strip() for x in table.locator("thead th").all_inner_texts()]
    rows = []
    for tr in table.locator("tbody tr").all():
        cells = [re.sub(r"\s+", " ", x).strip() for x in tr.locator("td").all_inner_texts()]
        if cells:
            rows.append(cells)
    return headers, rows

def pick_wanted_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Map actual columns -> wanted columns using keyword matching
    actual = list(df.columns)
    actual_norm = {c: norm(c) for c in actual}

    # helper to find best match by keywords
    def find_col(*keywords):
        kws = [k.upper() for k in keywords]
        for c in actual:
            s = actual_norm[c]
            if all(k in s for k in kws):
                return c
        return None

    col_map = {
        "PLAYER": find_col("PLAYER"),
        "BASE GROSS P/W (EUR)": find_col("BASE", "GROSS", "P/W"),
        "BASE GROSS P/Y (EUR)": find_col("BASE", "GROSS", "P/Y"),
        "BONUS GROSS P/Y (EUR)": find_col("BONUS", "GROSS", "P/Y"),
        "TOTAL GROSS P/Y (EUR)": find_col("TOTAL", "GROSS", "P/Y"),
        "SIGNED": find_col("SIGNED"),
        "EXPIRATION": find_col("EXPIRATION"),
        "YEARS REMAINING": find_col("YEARS", "REMAINING"),
        "GROSS REMAINING (EUR)": find_col("GROSS", "REMAINING"),
        "RELEASE CLAUSE (EUR)": find_col("RELEASE", "CLAUSE"),
    }

    keep = {new: old for new, old in col_map.items() if old is not None}
    out = df[list(keep.values())].copy()
    out.columns = list(keep.keys())

    for c in WANTED_COLS:
        if c not in out.columns:
            out[c] = ""

    return out[WANTED_COLS]

def main():
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) League page -> collect club base links
        page.goto(LEAGUE_PAYROLLS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        clubs = club_links_from_league_page(page)
        if not clubs:
            raise RuntimeError("Could not find any club links on payrolls page.")

        # 2) Visit each club salaries page
        for i, club_base in enumerate(clubs, start=1):
            club_salaries = to_salaries_url(club_base)
            print(f"[{i}/{len(clubs)}] {club_salaries}")

            page.goto(club_salaries, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

           
            click_if_exists(page, "EUR")
            click_if_exists(page, "GROSS")

# give Capology time to recalc values
            page.wait_for_timeout(1500)

            headers, rows = extract_contracts_table(page)
            print("Headers:", headers)
            print("First row length:", len(rows[0]) if rows else 0)
            if not rows:
                print("  -> No rows found (maybe paywalled or table not loaded).")
                continue

            df = pd.DataFrame(rows, columns=headers if headers and len(headers)==len(rows[0]) else None)
            df.insert(0, "CLUB_SALARIES_URL", club_salaries)

            df2 = pick_wanted_columns(df)
            df2.insert(0, "CLUB_SALARIES_URL", club_salaries)

            all_rows.append(df2)

            time.sleep(1.2)

        browser.close()

    if not all_rows:
        raise RuntimeError("No data scraped. Likely paywall or table selectors need adjustment.")

    final = pd.concat(all_rows, ignore_index=True)
    final.to_excel("capology_PL_contracts_columns.xlsx", index=False)
    print("Saved: capology_PL_contracts_columns.xlsx")

if __name__ == "__main__":
    main()