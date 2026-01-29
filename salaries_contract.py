import re
import time
import pandas as pd
from playwright.sync_api import sync_playwright

# ✅ PASTE ONLY THE CLUB SALARIES LINKS YOU WANT
CLUB_SALARIES_URLS = [
    "https://www.capology.com/club/ac-milan/salaries/",
    "https://www.capology.com/club/atalanta/salaries/",
    "https://www.capology.com/club/bologna/salaries/",
    "https://www.capology.com/club/cagliari/salaries/",
    "https://www.capology.com/club/como/salaries/",
    "https://www.capology.com/club/cremonese/salaries/",
    "https://www.capology.com/club/fiorentina/salaries/",
    "https://www.capology.com/club/genoa/salaries/",
    "https://www.capology.com/club/hellas-verona/salaries/",
    "https://www.capology.com/club/inter-milan/salaries/",
    "https://www.capology.com/club/juventus/salaries/",
    "https://www.capology.com/club/lazio/salaries/",
    "https://www.capology.com/club/lecce/salaries/",
    "https://www.capology.com/club/napoli/salaries/",
    "https://www.capology.com/club/parma/salaries/",
    "https://www.capology.com/club/pisa/salaries/",
    "https://www.capology.com/club/roma/salaries/",
    "https://www.capology.com/club/sassuolo/salaries/",
    "https://www.capology.com/club/torino/salaries/",
    "https://www.capology.com/club/udinese/salaries/"
    # add more...
]

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

def norm(x) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip()).upper()

def click_if_exists(page, text: str):
    loc = page.locator(f"button:has-text('{text}')")
    if loc.count() > 0:
        loc.first.click()
        page.wait_for_timeout(800)

def extract_best_contracts_table(page):
    # Wait for any table rows to appear
    page.wait_for_selector("table tbody tr", timeout=25000)

    tables = page.locator("table")
    best_table = None
    best_score = -1

    for i in range(tables.count()):
        t = tables.nth(i)

        headers = t.locator("thead th").all_inner_texts()
        headers_clean = [h.strip().lower() for h in headers if h.strip()]
        row_count = t.locator("tbody tr").count()

        if row_count == 0 or not headers_clean:
            continue

        joined = " ".join(headers_clean)

        # score: look for contracts-like columns
        score = 0
        for kw in ["player", "gross", "p/w", "p/y", "expiration", "remaining", "release"]:
            if kw in joined:
                score += 1
        score += min(row_count, 50) / 10

        if score > best_score:
            best_score = score
            best_table = t

    if best_table is None:
        return [], []

    # extract table via JS (gets rendered text)
    data = best_table.evaluate("""
    (tbl) => {
      const clean = (s) => (s || "").replace(/\\s+/g, " ").trim();
      const headers = Array.from(tbl.querySelectorAll("thead th")).map(th => clean(th.innerText));
      const rows = Array.from(tbl.querySelectorAll("tbody tr")).map(tr =>
        Array.from(tr.querySelectorAll("td")).map(td => clean(td.innerText))
      );
      return { headers, rows };
    }
    """)
    return data["headers"], data["rows"]

def pick_wanted_columns_by_index(rows: list[list[str]]) -> pd.DataFrame:
    records = []

    for r in rows:
        record = {
            "PLAYER": r[0] if len(r) > 0 else "",
            "BASE GROSS P/W (EUR)": r[2] if len(r) > 2 else "",
            "BASE GROSS P/Y (EUR)": r[3] if len(r) > 3 else "",
            "BONUS GROSS P/Y (EUR)": r[4] if len(r) > 4 else "",
            "TOTAL GROSS P/Y (EUR)": r[5] if len(r) > 5 else "",
            "SIGNED": r[6] if len(r) > 6 else "",
            "EXPIRATION": r[7] if len(r) > 7 else "",
            "YEARS REMAINING": r[8] if len(r) > 8 else "",
            "GROSS REMAINING (EUR)": r[9] if len(r) > 9 else "",
            "RELEASE CLAUSE (EUR)": ""
        }
        records.append(record)

    return pd.DataFrame(records)

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

    # build output with blanks for missing
    out = pd.DataFrame()
    for wanted in WANTED_COLS:
        src = col_map.get(wanted)
        out[wanted] = df[src] if src in df.columns else ""

    return out

def main():
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for idx, url in enumerate(CLUB_SALARIES_URLS, start=1):
            print(f"[{idx}/{len(CLUB_SALARIES_URLS)}] {url}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Force EUR + GROSS like your screenshot
            click_if_exists(page, "EUR")
            click_if_exists(page, "GROSS")
            page.wait_for_timeout(2000)

            headers, rows = extract_best_contracts_table(page)

            if idx == 1:
                print("DEBUG headers:", headers)
                print("DEBUG first row:", rows[0] if rows else "NO ROWS")

            if not rows:
                print("  -> No rows found (maybe paywalled or table didn’t load). Skipping.")
                continue

            # Make sure we always have usable headers
            if not headers or len(headers) != len(rows[0]):
                headers = [f"COL_{i}" for i in range(len(rows[0]))]

            df2 = pick_wanted_columns_by_index(rows)
            df2.insert(0, "CLUB_SALARIES_URL", url)
            all_rows.append(df2)
            time.sleep(1.0)

        browser.close()

    if not all_rows:
        raise RuntimeError("No data scraped from any pasted links.")

    final = pd.concat(all_rows, ignore_index=True)
    final.to_excel("capology_salaries_EUR.xlsx", index=False)
    print("Saved: capology_salaries_EUR.xlsx")

if __name__ == "__main__":
    main()