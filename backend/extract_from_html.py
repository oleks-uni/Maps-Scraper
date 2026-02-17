import re
from bs4 import BeautifulSoup

TIME_LIKE = re.compile(r"\b\d{1,2}:\d{2}\b")
STATUS_WORDS = (
    "Зачинено", "Відчиняється", "Відчинено", "Закрито",
    "Отворено", "Затваря",
    "Closed", "Open", "Opens", "Closes"
)

def extract_address(article):
    blocks = article.select("div.W4Efsd")
    for block in blocks:
        # пропускаємо саме рейтинг-блок (а не accessibility icons role=img)
        if block.select_one("span.ZkP5Je[aria-label]") or block.select_one("span.MW4etd"):
            continue

        text = block.get_text("\n", strip=True)
        if not text:
            continue

        for ln in [x.strip() for x in text.split("\n") if x.strip()]:
            if TIME_LIKE.search(ln) or any(w in ln for w in STATUS_WORDS):
                continue
            if any(ch.isdigit() for ch in ln):
                return ln
    return None


def parse_places(html: str):
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select('div[role="article"], div.Nv2PK')  # якщо inner_html - інколи Nv2PK без role

    results = []
    for a in articles:
        # name
        name = None
        name_tag = a.select_one('a[aria-label]')
        if name_tag and name_tag.get("aria-label"):
            name = name_tag["aria-label"].strip()
        elif a.get("aria-label"):
            name = a["aria-label"].strip()

        # rating raw (може бути різними мовами)
        rating_raw = None
        rating_tag = a.select_one('span.ZkP5Je[aria-label]')
        if rating_tag:
            rating_raw = rating_tag.get("aria-label")

        address = extract_address(a)

        if name:
            results.append({
                "name": name,
                "rating_info": rating_raw,
                "address": address
            })

    return results