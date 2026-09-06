#!/usr/bin/env python3
import json
import re
import html
import urllib.request
import urllib.parse
import datetime
import email.utils
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"

SOURCES = [
    {"name":"BOSS","url":"https://boss.gouv.fr/portail/accueil.html","kind":"OFFICIEL"},
    {"name":"Légifrance","url":"https://www.legifrance.gouv.fr/","kind":"OFFICIEL"},
    {"name":"URSSAF","url":"https://www.urssaf.fr/accueil/actualites.html","kind":"OFFICIEL"},
    {"name":"Net-entreprises","url":"https://www.net-entreprises.fr/","kind":"OFFICIEL"},
    {"name":"Ministère du Travail","url":"https://travail-emploi.gouv.fr/droit-du-travail","kind":"OFFICIEL"},
    {"name":"Service-Public Pro","url":"https://entreprendre.service-public.fr/","kind":"OFFICIEL"},
    {"name":"Assurance Maladie","url":"https://www.ameli.fr/entreprise","kind":"OFFICIEL"},
    {"name":"France Travail","url":"https://www.francetravail.fr/employeur/","kind":"OFFICIEL"},
    {"name":"Agirc-Arrco","url":"https://www.agirc-arrco.fr/entreprises/","kind":"OFFICIEL"},
    {"name":"Légisocial","url":"https://www.legisocial.fr/actualites-sociales/","kind":"EXPERT PAIE"},
    {"name":"RF Paye","url":"https://www.revue-fiduciaire.com/","kind":"EXPERT PAIE"},
    {"name":"Éditions Tissot","url":"https://www.editions-tissot.fr/actualite/droit-du-travail","kind":"EXPERT PAIE"},
]

KEYWORDS = [
    "paie","paye","bulletin","salaire","dsn","cotisation","cotisations","urssaf","boss",
    "smic","pmss","plafond sécurité sociale","plafond de la sécurité sociale","rgdu",
    "réduction générale","reduction generale","prélèvement à la source","prelevement a la source",
    "net social","montant net social","ijss","arrêt maladie","arret maladie","congés payés",
    "conges payes","avantage en nature","avantages en nature","frais professionnels",
    "rupture conventionnelle","licenciement","convention collective","heures supplémentaires",
    "heures supplementaires","retraite complémentaire","retraite complementaire","indemnité",
    "indemnite","employeur","salarié","salarie","prime","rémunération","remuneration"
]

EXCLUDED_TITLE_TERMS = [
    "mot de passe oublié","mot de passe oublie","connexion","se connecter","créer un compte",
    "creer un compte","mon compte","espace personnel","espace client","nous contacter",
    "mentions légales","mentions legales","politique de confidentialité","politique de confidentialite",
    "gestion des cookies","accessibilité","accessibilite","plan du site","newsletter",
    "s'abonner","abonnez-vous","formation","formations","certifiant","certification",
    "webinaire","webinaires","podcast","podcasts","vidéo","videos","vidéos","livre blanc",
    "boutique","commander","tarif","tarifs","abonnement","abonnez vous","offre d'emploi",
    "offres d'emploi","nos services","nos solutions"
]

EXCLUDED_URL_TERMS = [
    "/formation/","/formations/","/podcast","/video","/videos/","/boutique/",
    "/abonnement","/emploi/","/offre-emploi","/recrutement/"
]

NEWS_URL_HINTS = (
    "/actualit", "/actualites", "/actualite/", "/article/", "/articles/",
    "/news/", "/publication/", "/publications/", "/communique", "/information/"
)

FRESHNESS_DAYS = 365

# Certaines pages sont utiles comme documentation mais ne sont pas des actualités.
DOCUMENTATION_URL_TERMS = [
    "/declaration/api-dsn/",
    "/declaration/pilotes-dsn/",
    "/declaration/tables-de-nomenclatures/",
    "/declaration/comptes-rendus-metiers-dsn/",
    "/declaration/outils-de-controle-dsn-val/",
    "/declaration/entreprises-etrangeres/",
    "/declaration/declarations-msa-sante/",
    "/declaration/micro-entrepreneur/",
    "/declaration/crpcen/",
    "/declaration/dpae/",
]

TOPIC_RULES = [
    ("DSN", ("dsn","déclaration sociale nominative","declaration sociale nominative")),
    ("SMIC", ("smic",)),
    ("PMSS", ("pmss","plafond mensuel","plafond de la sécurité sociale","plafond securite sociale")),
    ("RGDU", ("rgdu","réduction générale","reduction generale")),
    ("IJSS", ("ijss","indemnités journalières","indemnites journalieres","arrêt maladie","arret maladie")),
    ("Cotisations", ("cotisation","cotisations","urssaf","boss")),
    ("Congés", ("congés payés","conges payes")),
    ("Rupture", ("rupture conventionnelle","licenciement","fin de contrat")),
    ("Rémunération", ("rémunération","remuneration","salaire","prime","bulletin de paie","bulletin de paye","paie")),
    ("PAS", ("prélèvement à la source","prelevement a la source")),
    ("Net social", ("net social","montant net social")),
    ("Retraite", ("retraite complémentaire","retraite complementaire","agirc-arrco")),
]

USER_AGENT = (
    "Mozilla/5.0 (compatible; VeilleJurSoc/4.5; "
    "+https://github.com/bastiaancampagne/VeilleJurSoc)"
)

def fetch(url, timeout=20):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache",
    }

    last_error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout + attempt * 5) as response:
                return response.read(), response.geturl()
        except Exception as exc:
            last_error = exc

    raise last_error

def clean_text(value):
    if not value:
        return ""
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def parse_date(value):
    if not value:
        return None
    value = value.strip()

    try:
        dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc).isoformat()
    except Exception:
        pass

    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt:
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc).isoformat()
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.datetime.strptime(value[:10], fmt)
            return dt.replace(tzinfo=datetime.timezone.utc).isoformat()
        except Exception:
            continue

    return None

def matched_topics(title, summary=""):
    text = clean_text(title + " " + summary).lower()
    return [
        label
        for label, terms in TOPIC_RULES
        if any(term in text for term in terms)
    ]

def looks_like_news_url(url):
    path = urllib.parse.urlparse(url or "").path.lower()
    return any(hint in path for hint in NEWS_URL_HINTS)

def is_excluded_url(url):
    lower_url = (url or "").lower()
    return any(term in lower_url for term in EXCLUDED_URL_TERMS)

def is_documentation_url(url):
    lower_url = (url or "").lower()
    return any(term in lower_url for term in DOCUMENTATION_URL_TERMS)

def is_fresh(published, days=FRESHNESS_DAYS):
    if not published:
        return True
    try:
        dt = datetime.datetime.fromisoformat(published)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        return cutoff <= dt <= datetime.datetime.now(datetime.timezone.utc)
    except Exception:
        return False

def relevant(title, summary="", url="", published=None):
    title_text = clean_text(title).lower()
    full_text = clean_text(title + " " + summary).lower()

    if len(clean_text(title)) < 20:
        return False

    if any(term in title_text for term in EXCLUDED_TITLE_TERMS):
        return False

    if is_excluded_url(url) or is_documentation_url(url):
        return False

    if published and not is_fresh(published):
        return False

    if not any(keyword.lower() in full_text for keyword in KEYWORDS):
        return False

    # Une page HTML sans date doit au moins ressembler à une vraie publication.
    if url and not published and not looks_like_news_url(url):
        return False

    return True

def extract_published_date(page):
    if not page:
        return None

    patterns = [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:published_time["\']',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']date["\']',
        r'<meta[^>]+name=["\']publish-date["\'][^>]+content=["\']([^"\']+)["\']',
        r'<time[^>]+datetime=["\']([^"\']+)["\']',
    ]

    now = datetime.datetime.now(datetime.timezone.utc)

    for pattern in patterns:
        match = re.search(pattern, page, flags=re.I | re.S)
        if not match:
            continue

        parsed = parse_date(html.unescape(match.group(1)))
        if not parsed:
            continue

        try:
            parsed_dt = datetime.datetime.fromisoformat(parsed)
            if parsed_dt <= now:
                return parsed
        except Exception:
            continue

    return None

def make_item(source, title, url, summary="", published=None):
    return {
        "title": clean_text(title),
        "url": url,
        "source": source["name"],
        "sourceKind": source["kind"],
        "summary": clean_text(summary),
        "publishedAt": published,
        "discoveredAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "topics": matched_topics(title, summary),
    }

def discover_feeds(page, base_url):
    feeds = []
    pattern = r'<link\b[^>]*type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)["\']'
    for match in re.finditer(pattern, page, flags=re.I | re.S):
        feeds.append(urllib.parse.urljoin(base_url, html.unescape(match.group(1))))
    # Variante où href apparaît avant type
    pattern2 = r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*type=["\']application/(?:rss|atom)\+xml["\']'
    for match in re.finditer(pattern2, page, flags=re.I | re.S):
        feeds.append(urllib.parse.urljoin(base_url, html.unescape(match.group(1))))
    return list(dict.fromkeys(feeds))[:5]

def parse_feed(raw, source):
    items = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return items

    # RSS
    for node in root.findall(".//item"):
        title = clean_text(node.findtext("title") or "")
        url = clean_text(node.findtext("link") or "")
        summary = clean_text(node.findtext("description") or "")
        published = parse_date(node.findtext("pubDate") or "")
        if title and url and relevant(title, summary, url, published):
            items.append(make_item(source, title, url, summary, published))

    # Atom
    ns_match = re.match(r"\{([^}]+)\}", root.tag or "")
    ns = {"a": ns_match.group(1)} if ns_match else {}
    entries = root.findall(".//a:entry", ns) if ns else root.findall(".//entry")

    for entry in entries:
        def findtext(name):
            node = entry.find(f"a:{name}", ns) if ns else entry.find(name)
            return node.text if node is not None and node.text else ""

        title = clean_text(findtext("title"))
        summary = clean_text(findtext("summary") or findtext("content"))
        published = parse_date(findtext("published") or findtext("updated"))

        url = ""
        links = entry.findall("a:link", ns) if ns else entry.findall("link")
        for link in links:
            href = link.attrib.get("href", "")
            rel = link.attrib.get("rel", "alternate")
            if href and rel in ("alternate", ""):
                url = href
                break

        if title and url and relevant(title, summary, url, published):
            items.append(make_item(source, title, url, summary, published))

    return items

def extract_description(page):
    patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page, flags=re.I | re.S)
        if match:
            return clean_text(html.unescape(match.group(1)))
    return ""

def extract_page_links(page, base_url, source):
    candidates = []
    seen = set()
    base_domain = urllib.parse.urlparse(base_url).netloc.lower()
    pattern = r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'

    for match in re.finditer(pattern, page, flags=re.I | re.S):
        href = html.unescape(match.group(1)).strip()
        title = clean_text(match.group(2))

        if len(title) < 20 or len(title) > 300:
            continue
        if any(term in title.lower() for term in EXCLUDED_TITLE_TERMS):
            continue
        if not any(keyword.lower() in title.lower() for keyword in KEYWORDS):
            continue

        url = urllib.parse.urljoin(base_url, href).split("#")[0]
        if not url.startswith(("http://", "https://")):
            continue
        if is_excluded_url(url):
            continue

        domain = urllib.parse.urlparse(url).netloc.lower()
        if base_domain and domain and not (
            domain == base_domain
            or domain.endswith("." + base_domain)
            or base_domain.endswith("." + domain)
        ):
            continue

        if url in seen:
            continue
        seen.add(url)
        candidates.append((title, url))

    results = []

    for title, url in candidates[:16]:
        summary = ""
        published = None

        try:
            raw, final_url = fetch(url, timeout=12)
            article_page = raw.decode("utf-8", errors="replace")
            url = final_url
            published = extract_published_date(article_page)
            summary = extract_description(article_page)
        except Exception:
            pass

        if relevant(title, summary, url, published):
            results.append(make_item(source, title, url, summary, published))

    return results

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    new_items = []
    errors = []

    for source in SOURCES:
        try:
            raw, final_url = fetch(source["url"])
            page = raw.decode("utf-8", errors="replace")

            source_items = []
            for feed_url in discover_feeds(page, final_url):
                try:
                    feed_raw, _ = fetch(feed_url, timeout=15)
                    source_items.extend(parse_feed(feed_raw, source))
                except Exception:
                    continue

            if not source_items:
                source_items = extract_page_links(page, final_url, source)

            new_items.extend(source_items)

        except Exception as exc:
            errors.append({
                "source": source["name"],
                "error": str(exc)[:300],
            })

    old_items = []
    if OUT.exists():
        try:
            old_payload = json.loads(OUT.read_text(encoding="utf-8"))
            old_items = old_payload.get("items", []) if isinstance(old_payload, dict) else []
        except Exception:
            old_items = []

    by_url = {}

    # Anciennes trouvailles : elles repassent dans le filtre v4.4.1.
    for item in old_items:
        url = item.get("url", "")
        published = item.get("publishedAt")
        if url and relevant(
            item.get("title", ""),
            item.get("summary", ""),
            url,
            published,
        ):
            item["topics"] = matched_topics(
                item.get("title", ""),
                item.get("summary", ""),
            )
            by_url[url] = item

    # Nouvelles trouvailles.
    for item in new_items:
        url = item.get("url")
        if not url:
            continue

        if url not in by_url:
            by_url[url] = item
            continue

        old = by_url[url]
        if len(item.get("summary", "")) > len(old.get("summary", "")):
            old["summary"] = item["summary"]
        if item.get("publishedAt"):
            old["publishedAt"] = item["publishedAt"]
        if item.get("title"):
            old["title"] = item["title"]
        old["topics"] = matched_topics(old.get("title", ""), old.get("summary", ""))

    items = list(by_url.values())

    # Nettoyer les dates futures et supprimer les publications datées
    # de plus de 90 jours. Les pages sans date ne sont conservées que
    # si elles ressemblent réellement à une actualité.
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=FRESHNESS_DAYS)
    cleaned_items = []

    for item in items:
        published = item.get("publishedAt")
        url = item.get("url", "")

        if is_documentation_url(url):
            continue

        if published:
            try:
                published_dt = datetime.datetime.fromisoformat(published)
                if not published_dt.tzinfo:
                    published_dt = published_dt.replace(tzinfo=datetime.timezone.utc)
                if published_dt > now or published_dt < cutoff:
                    continue
            except Exception:
                continue
        elif not looks_like_news_url(url):
            continue

        cleaned_items.append(item)

    items = cleaned_items

    # Les plus récentes d'abord pour faciliter le contrôle du JSON.
    items.sort(
        key=lambda item: (
            item.get("publishedAt") or item.get("discoveredAt") or ""
        ),
        reverse=True,
    )

    if len(items) > 1500:
        items = items[:1500]

    payload = {
        "generated_at": now.isoformat(),
        "items": items,
        "errors": errors,
    }

    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"VeilleJurSoc : {len(items)} trouvaille(s) conservée(s), "
        f"{len(new_items)} candidate(s) collectée(s), "
        f"{len(errors)} erreur(s)."
    )

if __name__ == "__main__":
    main()
