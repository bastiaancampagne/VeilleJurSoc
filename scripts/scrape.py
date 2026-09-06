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


# ---------------------------------------------------------
# Fichier dans lequel les trouvailles seront enregistrées
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"


# ---------------------------------------------------------
# Sources surveillées
# ---------------------------------------------------------

SOURCES = [
    {
        "name": "BOSS",
        "url": "https://boss.gouv.fr/portail/accueil.html",
        "kind": "OFFICIEL",
    },
    {
        "name": "Légifrance",
        "url": "https://www.legifrance.gouv.fr/",
        "kind": "OFFICIEL",
    },
    {
        "name": "URSSAF",
        "url": "https://www.urssaf.fr/accueil/actualites.html",
        "kind": "OFFICIEL",
    },
    {
        "name": "Net-entreprises",
        "url": "https://www.net-entreprises.fr/",
        "kind": "OFFICIEL",
    },
    {
        "name": "Ministère du Travail",
        "url": "https://travail-emploi.gouv.fr/droit-du-travail",
        "kind": "OFFICIEL",
    },
    {
        "name": "Service-Public Pro",
        "url": "https://entreprendre.service-public.fr/",
        "kind": "OFFICIEL",
    },
    {
        "name": "Assurance Maladie",
        "url": "https://www.ameli.fr/entreprise",
        "kind": "OFFICIEL",
    },
    {
        "name": "France Travail",
        "url": "https://www.francetravail.fr/employeur/",
        "kind": "OFFICIEL",
    },
    {
        "name": "Agirc-Arrco",
        "url": "https://www.agirc-arrco.fr/entreprises/",
        "kind": "OFFICIEL",
    },
    {
        "name": "Légisocial",
        "url": "https://www.legisocial.fr/actualites-sociales/",
        "kind": "EXPERT PAIE",
    },
    {
        "name": "RF Paye",
        "url": "https://www.revue-fiduciaire.com/",
        "kind": "EXPERT PAIE",
    },
    {
        "name": "Éditions Tissot",
        "url": "https://www.editions-tissot.fr/actualite/droit-du-travail",
        "kind": "EXPERT PAIE",
    },
]


# ---------------------------------------------------------
# Termes intéressants pour un gestionnaire de paie
# ---------------------------------------------------------

KEYWORDS = [
    "paie",
    "paye",
    "bulletin",
    "salaire",
    "dsn",
    "cotisation",
    "cotisations",
    "urssaf",
    "boss",
    "smic",
    "pmss",
    "plafond sécurité sociale",
    "plafond de la sécurité sociale",
    "rgdu",
    "réduction générale",
    "reduction generale",
    "pas",
    "prélèvement à la source",
    "prelevement a la source",
    "net social",
    "montant net social",
    "ijss",
    "arrêt maladie",
    "arret maladie",
    "congés payés",
    "conges payes",
    "avantage en nature",
    "avantages en nature",
    "frais professionnels",
    "rupture conventionnelle",
    "rupture",
    "licenciement",
    "convention collective",
    "heures supplémentaires",
    "heures supplementaires",
    "retraite complémentaire",
    "retraite complementaire",
    "indemnité",
    "indemnite",
    "employeur",
    "salarié",
    "salarie",
    "prime",
    "rémunération",
    "remuneration",
]
EXCLUDED_TERMS = [
    "mot de passe oublié",
    "mot de passe oublie",
    "connexion",
    "se connecter",
    "créer un compte",
    "creer un compte",
    "mon compte",
    "espace personnel",
    "espace client",
    "contact",
    "nous contacter",
    "mentions légales",
    "mentions legales",
    "politique de confidentialité",
    "politique de confidentialite",
    "cookies",
    "gestion des cookies",
    "accessibilité",
    "accessibilite",
    "plan du site",
    "newsletter",
    "s'abonner",
    "abonnez-vous",
    "accueil",
]

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; VeilleJurSoc/4.3; "
    "+https://github.com/bastiaancampagne/VeilleJurSoc)"
)


# ---------------------------------------------------------
# Téléchargement d'une page
# ---------------------------------------------------------

def fetch(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.geturl()


# ---------------------------------------------------------
# Nettoyage du texte HTML
# ---------------------------------------------------------

def clean_text(value):
    if not value:
        return ""

    value = re.sub(
        r"<script\b.*?</script>",
        " ",
        value,
        flags=re.I | re.S,
    )

    value = re.sub(
        r"<style\b.*?</style>",
        " ",
        value,
        flags=re.I | re.S,
    )

    value = re.sub(r"<[^>]+>", " ", value)

    value = html.unescape(value)

    return re.sub(r"\s+", " ", value).strip()


# ---------------------------------------------------------
# Vérifier si un contenu concerne la paie / le social
# ---------------------------------------------------------

def relevant(title, summary=""):
    text = clean_text(title + " " + summary).lower()

    # Éliminer les liens de navigation et de compte
    if any(term in text for term in EXCLUDED_TERMS):
        return False

    # Un titre trop court est rarement une véritable actualité
    if len(clean_text(title)) < 20:
        return False

    # Le contenu doit réellement concerner la paie ou le social
    return any(keyword.lower() in text for keyword in KEYWORDS)


# ---------------------------------------------------------
# Conversion d'une date
# ---------------------------------------------------------

def parse_date(value):
    if not value:
        return None

    value = value.strip()

    try:
        date = email.utils.parsedate_to_datetime(value)

        if date:
            if not date.tzinfo:
                date = date.replace(
                    tzinfo=datetime.timezone.utc
                )

            return date.astimezone(
                datetime.timezone.utc
            ).isoformat()

    except Exception:
        pass

    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            date = datetime.datetime.strptime(
                value[:25],
                fmt,
            )

            if not date.tzinfo:
                date = date.replace(
                    tzinfo=datetime.timezone.utc
                )

            return date.astimezone(
                datetime.timezone.utc
            ).isoformat()

        except Exception:
            continue

    return None


# ---------------------------------------------------------
# Création d'une trouvaille
# ---------------------------------------------------------

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

    for pattern in patterns:
        match = re.search(
            pattern,
            page,
            flags=re.I | re.S,
        )

        if match:
            parsed = parse_date(
                html.unescape(
                    match.group(1)
                )
            )

            if parsed:
                try:
                    parsed_dt = datetime.datetime.fromisoformat(parsed)

                    now = datetime.datetime.now(
                        datetime.timezone.utc
                    )

                    # Refuser les dates situées dans le futur
                    if parsed_dt <= now:
                        return parsed

                except Exception:
                    pass

    return None

def make_item(source, title, url, summary="", published_at=None):
    return {
        "title": title[:300],
        "url": url,
        "source": source["name"],
        "sourceKind": source["kind"],
        "summary": summary[:1000],
        "publishedAt": published_at,
        "discoveredAt": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
    }


# ---------------------------------------------------------
# Recherche automatique d'un flux RSS ou Atom
# ---------------------------------------------------------

def discover_feeds(page, base_url):
    feeds = []

    pattern = (
        r'<link[^>]+'
        r'type=["\']application/'
        r'(?:rss\+xml|atom\+xml)["\']'
        r'[^>]*>'
    )

    for match in re.finditer(
        pattern,
        page,
        flags=re.I,
    ):
        tag = match.group(0)

        href_match = re.search(
            r'href=["\']([^"\']+)["\']',
            tag,
            flags=re.I,
        )

        if href_match:
            href = html.unescape(
                href_match.group(1)
            )

            feeds.append(
                urllib.parse.urljoin(
                    base_url,
                    href,
                )
            )

    return feeds[:3]


# ---------------------------------------------------------
# Lecture d'un flux RSS ou Atom
# ---------------------------------------------------------

def parse_feed(raw, source):
    results = []

    try:
        root = ET.fromstring(raw)

    except Exception:
        return results

    # RSS
    for node in root.findall(".//item"):
        title = clean_text(
            node.findtext("title") or ""
        )

        url = (
            node.findtext("link") or ""
        ).strip()

        summary = clean_text(
            node.findtext("description") or ""
        )

        published = parse_date(
            node.findtext("pubDate")
            or node.findtext(
                "{http://purl.org/dc/elements/1.1/}date"
            )
            or ""
        )

        if title and url and relevant(title, summary):
            results.append(
                make_item(
                    source,
                    title,
                    url,
                    summary,
                    published,
                )
            )

    # Atom
    atom = "{http://www.w3.org/2005/Atom}"

    for node in root.findall(".//" + atom + "entry"):
        title = clean_text(
            node.findtext(atom + "title") or ""
        )

        summary = clean_text(
            node.findtext(atom + "summary")
            or node.findtext(atom + "content")
            or ""
        )

        url = ""

        for link in node.findall(atom + "link"):
            href = link.attrib.get("href", "")

            rel = link.attrib.get(
                "rel",
                "alternate",
            )

            if href and rel in (
                "",
                "alternate",
            ):
                url = href
                break

        published = parse_date(
            node.findtext(atom + "updated")
            or node.findtext(atom + "published")
            or ""
        )

        if title and url and relevant(title, summary):
            results.append(
                make_item(
                    source,
                    title,
                    url,
                    summary,
                    published,
                )
            )

    return results


# ---------------------------------------------------------
# Méthode de secours : recherche de liens dans la page
# ---------------------------------------------------------

def extract_page_links(page, base_url, source):
    candidates = []
    seen = set()

    pattern = (
        r'<a\b[^>]*'
        r'href=["\']([^"\']+)["\']'
        r'[^>]*>(.*?)</a>'
    )

    base_domain = urllib.parse.urlparse(
        base_url
    ).netloc.lower()

    for match in re.finditer(
        pattern,
        page,
        flags=re.I | re.S,
    ):
        href = html.unescape(
            match.group(1)
        ).strip()

        title = clean_text(
            match.group(2)
        )

        if len(title) < 20:
            continue

        if len(title) > 300:
            continue

        if not relevant(title):
            continue

        url = urllib.parse.urljoin(
            base_url,
            href,
        )

        if not url.startswith(
            ("http://", "https://")
        ):
            continue

        # Éviter de sortir inutilement du site surveillé
        domain = urllib.parse.urlparse(
            url
        ).netloc.lower()

        if (
            base_domain
            and domain
            and not (
                domain == base_domain
                or domain.endswith("." + base_domain)
                or base_domain.endswith("." + domain)
            )
        ):
            continue

        # Éviter les doublons
        clean_url = url.split("#")[0]

        if clean_url in seen:
            continue

        seen.add(clean_url)

        candidates.append(
            {
                "title": title,
                "url": clean_url,
            }
        )

    results = []

    # On limite le nombre de pages ouvertes
    # pour ne pas ralentir excessivement GitHub Actions.
    for candidate in candidates[:12]:
        title = candidate["title"]
        url = candidate["url"]

        summary = ""
        published = None

        try:
            article_raw, final_url = fetch(
                url,
                timeout=12,
            )

            article_page = article_raw.decode(
                "utf-8",
                errors="replace",
            )

            published = extract_published_date(
                article_page
            )

            # Essayer de récupérer une description
            description_patterns = [
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
            ]

            for description_pattern in description_patterns:
                description_match = re.search(
                    description_pattern,
                    article_page,
                    flags=re.I | re.S,
                )

                if description_match:
                    summary = clean_text(
                        html.unescape(
                            description_match.group(1)
                        )
                    )
                    break

            url = final_url

        except Exception:
            pass

        results.append(
            make_item(
                source,
                title,
                url,
                summary,
                published,
            )
        )

    return results

# ---------------------------------------------------------
# Programme principal
# ---------------------------------------------------------

def main():
    new_items = []
    errors = []

    for source in SOURCES:
        print(
            "Lecture de",
            source["name"],
            "..."
        )

        try:
            raw, final_url = fetch(
                source["url"]
            )

            page = raw.decode(
                "utf-8",
                errors="replace",
            )

            source_items = []

            # Priorité aux flux RSS/Atom
            feeds = discover_feeds(
                page,
                final_url,
            )

            for feed_url in feeds:
                try:
                    feed_raw, _ = fetch(
                        feed_url
                    )

                    source_items.extend(
                        parse_feed(
                            feed_raw,
                            source,
                        )
                    )

                except Exception:
                    pass

            # Si aucun flux exploitable,
            # recherche dans la page HTML
            if not source_items:
                source_items.extend(
                    extract_page_links(
                        page,
                        final_url,
                        source,
                    )
                )

            print(
                "  ->",
                len(source_items),
                "trouvaille(s)",
            )

            new_items.extend(
                source_items
            )

        except Exception as error:
            print(
                "  ERREUR :",
                error,
            )

            errors.append(
                {
                    "source": source["name"],
                    "error": str(error)[:300],
                }
            )

    # -----------------------------------------------------
    # Récupérer les anciennes archives
    # -----------------------------------------------------

    old_items = []

    if OUT.exists():
        try:
            existing = json.loads(
                OUT.read_text(
                    encoding="utf-8"
                )
            )

            old_items = existing.get(
                "items",
                [],
            )

        except Exception:
            old_items = []

    # -----------------------------------------------------
    # Fusion sans doublons
    # -----------------------------------------------------

    by_url = {}

    for item in old_items:
        url = item.get("url")

        if url:
            by_url[url] = item

    for item in new_items:
        url = item.get("url")

        if not url:
            continue

        if url not in by_url:
            by_url[url] = item

        else:
            old = by_url[url]

            if (
                len(item.get("summary", ""))
                >
                len(old.get("summary", ""))
            ):
                old["summary"] = item.get(
                    "summary",
                    "",
                )

            if item.get("publishedAt"):
                old["publishedAt"] = item[
                    "publishedAt"
                ]

            if item.get("title"):
                old["title"] = item[
                    "title"
                ]

    items = list(
        by_url.values()
    )
    
    # Nettoyer également les anciennes trouvailles
    items = [
        item for item in items
        if relevant(
            item.get("title", ""),
            item.get("summary", "")
        )
    ]

    # Maximum 1500 trouvailles
    if len(items) > 1500:
        items = items[-1500:]

    # -----------------------------------------------------
    # Enregistrer news.json
    # -----------------------------------------------------

    payload = {
        "generated_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "items": items,
        "errors": errors,
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        len(new_items),
        "trouvaille(s) détectée(s)",
    )

    print(
        len(items),
        "trouvaille(s) conservée(s)",
    )

    print(
        len(errors),
        "source(s) en erreur",
    )


if __name__ == "__main__":
    main()
