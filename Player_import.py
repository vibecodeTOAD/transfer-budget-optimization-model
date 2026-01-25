import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.transfermarkt.co.in/"
}

session = requests.Session()
session.headers.update(HEADERS)

def scrape_tm_squad(url: str) -> pd.DataFrame:
    r = session.get(url, timeout=(10, 30))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table", class_="items")
    if table is None:
        title = soup.title.get_text(strip=True) if soup.title else "No title"
        raise ValueError(f"No squad table found | Page title: {title}")

    rows = []
    for tr in table.select("tr.odd, tr.even"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue

        player = tds[1].get_text(" ", strip=True)
        contract = tds[-2].get_text(" ", strip=True)
        market_value = tds[-1].get_text(" ", strip=True)

        rows.append({
            "player": player,
            "contract": contract,
            "market_value": market_value,
            "source_url": url
        })

    return pd.DataFrame(rows)


tm_urls = [
    "https://www.transfermarkt.co.in/manchester-city/kader/verein/281/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/arsenal-fc/kader/verein/11/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/chelsea-fc/kader/verein/631/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/liverpool-fc/kader/verein/31/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/tottenham-hotspur/kader/verein/148/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/manchester-united/kader/verein/985/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/newcastle-united/kader/verein/762/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/nottingham-forest/kader/verein/703/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/brighton-amp-hove-albion/kader/verein/1237/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/aston-villa/kader/verein/405/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/crystal-palace/kader/verein/873/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/brentford-fc/kader/verein/1148/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/afc-bournemouth/kader/verein/989/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/everton-fc/kader/verein/29/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/west-ham-united/kader/verein/379/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/sunderland-afc/kader/verein/289/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/fulham-fc/kader/verein/931/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/wolverhampton-wanderers/kader/verein/543/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/leeds-united/kader/verein/399/saison_id/2025/plus/1",
    "https://www.transfermarkt.co.in/burnley-fc/kader/verein/1132/saison_id/2025/plus/1"
]

all_data = []
failed = []

for i, u in enumerate(tm_urls, start=1):
    print(f"[{i}/{len(tm_urls)}] Scraping: {u}")
    try:
        df = scrape_tm_squad(u)
        print(f"   → players scraped: {len(df)}")
        all_data.append(df)
    except Exception as e:
        print(f"   !! failed: {e}")
        failed.append({"url": u, "error": str(e)})

    time.sleep(2)  # polite delay to avoid blocking

final_tm = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
final_tm.to_excel("transfermarkt_multi_clubs.xlsx", index=False)

if failed:
    pd.DataFrame(failed).to_excel("transfermarkt_failed_urls.xlsx", index=False)

print("DONE ✅")
print("Saved: transfermarkt_multi_clubs.xlsx")
print("Saved: transfermarkt_failed_urls.xlsx (only if failures occurred)")