#!/usr/bin/env python3
import json, re, html, urllib.request, urllib.parse, datetime, email.utils
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'news.json'
SOURCES=[
 {'name':'BOSS','url':'https://boss.gouv.fr/portail/accueil.html','kind':'OFFICIEL'},
 {'name':'Légifrance','url':'https://www.legifrance.gouv.fr/','kind':'OFFICIEL'},
 {'name':'URSSAF','url':'https://www.urssaf.fr/accueil/actualites.html','kind':'OFFICIEL'},
 {'name':'Net-entreprises','url':'https://www.net-entreprises.fr/','kind':'OFFICIEL'},
 {'name':'Ministère du Travail','url':'https://travail-emploi.gouv.fr/droit-du-travail','kind':'OFFICIEL'},
 {'name':'Service-Public Pro','url':'https://entreprendre.service-public.fr/','kind':'OFFICIEL'},
 {'name':'Assurance Maladie','url':'https://www.ameli.fr/entreprise','kind':'OFFICIEL'},
 {'name':'France Travail','url':'https://www.francetravail.fr/employeur/','kind':'OFFICIEL'},
 {'name':'Agirc-Arrco','url':'https://www.agirc-arrco.fr/entreprises/','kind':'OFFICIEL'},
 {'name':'Légisocial','url':'https://www.legisocial.fr/actualites-sociales/','kind':'EXPERT PAIE'},
 {'name':'RF Paye','url':'https://www.revue-fiduciaire.com/','kind':'EXPERT PAIE'},
 {'name':'Éditions Tissot','url':'https://www.editions-tissot.fr/actualite/droit-du-travail','kind':'EXPERT PAIE'}]
KEYWORDS=['paie','paye','bulletin','salaire','dsn','cotisation','cotisations','urssaf','boss','smic','pmss','plafond sécurité sociale','plafond de la sécurité sociale','rgdu','réduction générale','reduction generale','prélèvement à la source','prelevement a la source','net social','montant net social','ijss','arrêt maladie','arret maladie','congés payés','conges payes','avantage en nature','avantages en nature','frais professionnels','rupture conventionnelle','licenciement','convention collective','heures supplémentaires','heures supplementaires','retraite complémentaire','retraite complementaire','indemnité','indemnite','employeur','salarié','salarie','prime','rémunération','remuneration']
EXCLUDED_TERMS=['mot de passe oublié','mot de passe oublie','connexion','se connecter','créer un compte','creer un compte','mon compte','espace personnel','espace client','contact','nous contacter','mentions légales','mentions legales','politique de confidentialité','politique de confidentialite','cookies','gestion des cookies','accessibilité','accessibilite','plan du site','newsletter',"s'abonner",'abonnez-vous','accueil']
UA='Mozilla/5.0 (compatible; VeilleJurSoc/4.3; +https://github.com/bastiaancampagne/VeilleJurSoc)'

def fetch(url,timeout=20):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.geturl()
def clean_text(v):
 if not v:return ''
 v=re.sub(r'<script\b.*?</script>',' ',v,flags=re.I|re.S);v=re.sub(r'<style\b.*?</style>',' ',v,flags=re.I|re.S);v=re.sub(r'<[^>]+>',' ',v)
 return re.sub(r'\s+',' ',html.unescape(v)).strip()
def relevant(title,summary=''):
 text=clean_text(title+' '+summary).lower()
 if any(x in text for x in EXCLUDED_TERMS) or len(clean_text(title))<20:return False
 return any(k.lower() in text for k in KEYWORDS)
def parse_date(v):
 if not v:return None
 v=v.strip()
 try:
  d=email.utils.parsedate_to_datetime(v)
  if d:
   if not d.tzinfo:d=d.replace(tzinfo=datetime.timezone.utc)
   return d.astimezone(datetime.timezone.utc).isoformat()
 except Exception:pass
 for fmt in ('%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%d','%d/%m/%Y'):
  try:
   d=datetime.datetime.strptime(v[:25],fmt)
   if not d.tzinfo:d=d.replace(tzinfo=datetime.timezone.utc)
   return d.astimezone(datetime.timezone.utc).isoformat()
  except Exception:pass
 return None
def extract_published_date(page):
 patterns=[r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:published_time["\']',r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']date["\']',r'<meta[^>]+name=["\']publish-date["\'][^>]+content=["\']([^"\']+)["\']',r'<time[^>]+datetime=["\']([^"\']+)["\']']
 now=datetime.datetime.now(datetime.timezone.utc)
 for p in patterns:
  m=re.search(p,page,flags=re.I|re.S)
  if m:
   parsed=parse_date(html.unescape(m.group(1)))
   if parsed:
    try:
     if datetime.datetime.fromisoformat(parsed)<=now:return parsed
    except Exception:pass
 return None
def make_item(source,title,url,summary='',published=None):
 return {'title':title[:300],'url':url,'source':source['name'],'sourceKind':source['kind'],'summary':summary[:1000],'publishedAt':published,'discoveredAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def discover_feeds(page,base):
 out=[]
 for m in re.finditer(r'<link[^>]+type=["\']application/(?:rss\+xml|atom\+xml)["\'][^>]*>',page,flags=re.I):
  h=re.search(r'href=["\']([^"\']+)["\']',m.group(0),flags=re.I)
  if h:out.append(urllib.parse.urljoin(base,html.unescape(h.group(1))))
 return out[:3]
def parse_feed(raw,source):
 out=[]
 try:root=ET.fromstring(raw)
 except Exception:return out
 for n in root.findall('.//item'):
  title=clean_text(n.findtext('title') or '');url=(n.findtext('link') or '').strip();summary=clean_text(n.findtext('description') or '')
  pub=parse_date(n.findtext('pubDate') or n.findtext('{http://purl.org/dc/elements/1.1/}date') or '')
  if title and url and relevant(title,summary):out.append(make_item(source,title,url,summary,pub))
 atom='{http://www.w3.org/2005/Atom}'
 for n in root.findall('.//'+atom+'entry'):
  title=clean_text(n.findtext(atom+'title') or '');summary=clean_text(n.findtext(atom+'summary') or n.findtext(atom+'content') or '');url=''
  for link in n.findall(atom+'link'):
   if link.attrib.get('href') and link.attrib.get('rel','alternate') in ('','alternate'):url=link.attrib['href'];break
  pub=parse_date(n.findtext(atom+'updated') or n.findtext(atom+'published') or '')
  if title and url and relevant(title,summary):out.append(make_item(source,title,url,summary,pub))
 return out
def extract_page_links(page,base,source):
 candidates=[];seen=set();base_domain=urllib.parse.urlparse(base).netloc.lower()
 for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,flags=re.I|re.S):
  title=clean_text(m.group(2));href=html.unescape(m.group(1)).strip()
  if len(title)<20 or len(title)>300 or not relevant(title):continue
  url=urllib.parse.urljoin(base,href);domain=urllib.parse.urlparse(url).netloc.lower()
  if not url.startswith(('http://','https://')):continue
  if base_domain and domain and not(domain==base_domain or domain.endswith('.'+base_domain) or base_domain.endswith('.'+domain)):continue
  url=url.split('#')[0]
  if url in seen:continue
  seen.add(url);candidates.append((title,url))
 out=[]
 for title,url in candidates[:12]:
  summary='';pub=None
  try:
   raw,final=fetch(url,12);page2=raw.decode('utf-8',errors='replace');pub=extract_published_date(page2);url=final
   for p in [r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']']:
    dm=re.search(p,page2,flags=re.I|re.S)
    if dm:summary=clean_text(html.unescape(dm.group(1)));break
  except Exception:pass
  if relevant(title,summary):out.append(make_item(source,title,url,summary,pub))
 return out

def main():
 new=[];errors=[]
 for source in SOURCES:
  print('Lecture de',source['name'],'...')
  try:
   raw,final=fetch(source['url']);page=raw.decode('utf-8',errors='replace');found=[]
   for feed in discover_feeds(page,final):
    try:fr,_=fetch(feed);found.extend(parse_feed(fr,source))
    except Exception:pass
   if not found:found=extract_page_links(page,final,source)
   print(' ->',len(found),'trouvaille(s)');new.extend(found)
  except Exception as e:
   print(' ERREUR:',e);errors.append({'source':source['name'],'error':str(e)[:300]})
 old=[]
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8')).get('items',[])
  except Exception:pass
 by_url={i.get('url'):i for i in old if i.get('url')}
 for i in new:
  u=i.get('url')
  if not u:continue
  if u not in by_url:by_url[u]=i
  else:
   o=by_url[u]
   if len(i.get('summary',''))>len(o.get('summary','')):o['summary']=i.get('summary','')
   if i.get('publishedAt'):o['publishedAt']=i['publishedAt']
   if i.get('title'):o['title']=i['title']
 items=[i for i in by_url.values() if relevant(i.get('title',''),i.get('summary',''))]
 now=datetime.datetime.now(datetime.timezone.utc)
 for i in items:
  p=i.get('publishedAt')
  if p:
   try:
    if datetime.datetime.fromisoformat(p)>now:i['publishedAt']=None
   except Exception:i['publishedAt']=None
 def sortkey(i):return i.get('publishedAt') or i.get('discoveredAt') or ''
 items=sorted(items,key=sortkey,reverse=True)[:1500]
 payload={'generated_at':now.isoformat(),'items':items,'errors':errors}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 print(len(new),'trouvaille(s) détectée(s)');print(len(items),'trouvaille(s) conservée(s)');print(len(errors),'source(s) en erreur')
if __name__=='__main__':main()
