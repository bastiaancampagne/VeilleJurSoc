const SOURCES=[
 ["BOSS","https://boss.gouv.fr/portail/accueil.html","boss.gouv.fr","OFFICIEL"],
 ["Légifrance","https://www.legifrance.gouv.fr/","legifrance.gouv.fr","OFFICIEL"],
 ["URSSAF","https://www.urssaf.fr/accueil/actualites.html","urssaf.fr","OFFICIEL"],
 ["Net-entreprises","https://www.net-entreprises.fr/","net-entreprises.fr","OFFICIEL"],
 ["Ministère du Travail","https://travail-emploi.gouv.fr/droit-du-travail","travail-emploi.gouv.fr","OFFICIEL"],
 ["Service-Public Pro","https://entreprendre.service-public.fr/","service-public.fr","OFFICIEL"],
 ["Assurance Maladie","https://www.ameli.fr/entreprise","ameli.fr","OFFICIEL"],
 ["France Travail","https://www.francetravail.fr/employeur/","francetravail.fr","OFFICIEL"],
 ["Agirc-Arrco","https://www.agirc-arrco.fr/entreprises/","agirc-arrco.fr","OFFICIEL"],
 ["Légisocial","https://www.legisocial.fr/actualites-sociales/","legisocial.fr","EXPERT PAIE"],
 ["RF Paye","https://www.revue-fiduciaire.com/","revue-fiduciaire.com","EXPERT PAIE"],
 ["Éditions Tissot","https://www.editions-tissot.fr/actualite/droit-du-travail","editions-tissot.fr","EXPERT PAIE"]
];
const REMOTE_NEWS_URL="https://raw.githubusercontent.com/bastiaancampagne/VeilleJurSoc/main/data/news.json";
const DEFAULT_FAV=["DSN","SMIC","RGDU","IJSS","Rupture conventionnelle","Net social"];
const $=s=>document.querySelector(s), app=$("#app");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const norm=s=>String(s??"").normalize("NFD").replace(/\p{Diacritic}/gu,"").toLowerCase();
const getJSON=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
const setJSON=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
const favorites=()=>getJSON("vjs_favorites",DEFAULT_FAV);
const articles=()=>getJSON("vjs_articles",[]);
const toast=m=>{const t=$("#toast");t.textContent=m;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2600)};
const todayStart=()=>{const d=new Date();d.setHours(0,0,0,0);return +d};
const stamp=t=>t?new Intl.DateTimeFormat("fr-FR",{dateStyle:"short",timeStyle:"short"}).format(new Date(t)):"Date de publication non indiquée";
const setScene=name=>{
 document.body.dataset.scene=name;
 document.querySelectorAll(".navbtn").forEach(b=>b.classList.remove("active"));
 const map={home:"navHome",today:"navToday",archives:"navArchives",favorites:"navFavorites",sources:"navSources"};
 if(map[name])document.getElementById(map[name])?.classList.add("active");
};
const articleText=a=>`${a.title||""} ${a.summary||""} ${a.source||""} ${(a.topics||[]).join(" ")}`;
const CLIENT_EXCLUDED=["injonction de payer"];
function clientRelevant(a){const n=norm(articleText(a));return !CLIENT_EXCLUDED.some(x=>n.includes(norm(x)))}
function sortNewest(a,b){return (Number(b.publishedAt)||Number(b.discoveredAt)||0)-(Number(a.publishedAt)||Number(a.discoveredAt)||0)}
function sortArchives(a,b){const ap=Number(a.publishedAt)||0,bp=Number(b.publishedAt)||0;if(Boolean(ap)!==Boolean(bp))return bp?1:-1;return sortNewest(a,b)}
function termMatches(a,term){
 const t=norm(term).trim(); if(!t)return false;
 const hay=norm(articleText(a));
 if(t.length<=3){const safe=t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");return new RegExp(`(^|[^a-z0-9])${safe}([^a-z0-9]|$)`,`i`).test(hay)}
 return hay.includes(t);
}
function isFav(a){return favorites().some(x=>termMatches(a,x))}
function renderTopics(a){const topics=Array.isArray(a.topics)?a.topics.filter(Boolean):[];return topics.length?`<div class="topicrow">${topics.map(t=>`<span class="topic">${esc(t)}</span>`).join("")}</div>`:""}
function renderArticles(list,{empty="Aucune trouvaille enregistrée."}={}){
 if(!list.length)return `<div class="empty glass">${esc(empty)}</div>`;
 return [...list].map(a=>`<article class="card glass" data-url="${esc(a.url)}">
   <h3>${isFav(a)?'<span class="star">★ </span>':''}${esc(a.title)}</h3>
   <div class="meta">${esc(a.source)} • ${esc(a.sourceKind)} • ${stamp(a.publishedAt)}</div>
   ${renderTopics(a)}
   ${a.summary?`<p class="summary">${esc(a.summary)}</p>`:""}
   <a href="${esc(a.url)}" target="_blank" rel="noopener">Ouvrir l’article ↗</a>
 </article>`).join("");
}
function toTime(value){if(!value)return 0;if(typeof value==="number")return value;const t=Date.parse(value);return Number.isFinite(t)?t:0}
function normalizeArticle(a){return {...a,publishedAt:toTime(a.publishedAt),discoveredAt:toTime(a.discoveredAt)}}
async function syncCollectedNews(showMessage=true){
 try{
  const response=await fetch(REMOTE_NEWS_URL+"?t="+Date.now(),{cache:"no-store"});
  if(!response.ok)throw new Error("HTTP "+response.status);
  const data=await response.json();
  const remote=(Array.isArray(data.items)?data.items:[]).map(normalizeArticle).filter(a=>a.url&&clientRelevant(a));
  const manual=articles().map(normalizeArticle).filter(a=>a.manual===true&&a.url);
  const byUrl=new Map(remote.map(a=>[a.url,a]));
  manual.forEach(a=>{if(!byUrl.has(a.url))byUrl.set(a.url,a)});
  setJSON("vjs_articles",[...byUrl.values()]);
  const refreshDate=data.generated_at?new Date(data.generated_at):new Date();
  localStorage.setItem("vjs_last_refresh",new Intl.DateTimeFormat("fr-FR",{dateStyle:"short",timeStyle:"short"}).format(refreshDate));
  if(showMessage)toast("Veille actualisée");
  return true;
 }catch(error){console.error("Synchronisation VeilleJurSoc :",error);if(showMessage)toast("Impossible d’actualiser. Données locales conservées.");return false}
}
function showHome(){
 setScene("home");
 app.innerHTML=`<section class="panel glass home-panel"><h1 class="title">VeilleJurSoc</h1>
 <p class="subtitle">Votre veille juridique et sociale pour les professionnels de la paie</p>
 <p class="gag">🧮 Un émeu bien informé en vaut deux !</p>
 <div class="stack">
  <div class="searchrow"><input id="homeSearch" placeholder="Rechercher : DSN, SMIC, IJSS, RGDU…"><button class="action green" id="searchGo">🔎 Recherche</button></div>
  <button class="action blue" id="today">📰 Aujourd’hui</button>
  <button class="action green" id="archives">🗄️ Archives</button>
  <button class="action gold" id="favorites">★ Mes sujets favoris</button>
  <button class="action purple" id="sources">🔗 Les 12 sources</button>
 </div>
 <p class="muted">Dernière mise à jour : ${esc(localStorage.getItem("vjs_last_refresh")||"jamais")}</p>
 <p class="note">Les trouvailles sont synchronisées depuis le collecteur GitHub. Les anciennes données locales qui ne figurent plus dans la veille sont automatiquement purgées.</p></section>`;
 $("#searchGo").onclick=async()=>{await syncCollectedNews(false);showSearch($("#homeSearch").value.trim())};
 $("#homeSearch").onkeydown=async e=>{if(e.key==="Enter"){await syncCollectedNews(false);showSearch(e.target.value.trim())}};
 $("#today").onclick=async()=>{await syncCollectedNews(false);showArticles(false)};
 $("#archives").onclick=async()=>{await syncCollectedNews(false);showArticles(true)};
 $("#favorites").onclick=async()=>{await syncCollectedNews(false);showFavorites()};
 $("#sources").onclick=showSources;
}
function showArticles(archive){
 setScene(archive?"archives":"today");
 const start=todayStart(), tomorrow=start+86400000;
 const all=articles().filter(clientRelevant);
 const datedToday=all.filter(a=>{const p=Number(a.publishedAt)||0;return p>=start&&p<tomorrow}).sort(sortNewest);
 const datedOlder=all.filter(a=>{const p=Number(a.publishedAt)||0;return p&&p<start}).sort(sortNewest);
 const undated=all.filter(a=>!Number(a.publishedAt)).sort(sortNewest);
 if(archive){
  const list=[...datedOlder,...undated];
  app.innerHTML=`<section class="panel glass"><h1 class="section-title">🗄️ Archives</h1>
   <div class="toolbar"><button class="action blue" id="refresh">↻ Actualiser les trouvailles</button><button class="action green" id="add">＋ Ajouter un article</button></div>
   <p class="muted">${list.length} trouvaille(s) • articles datés d’abord, dates inconnues en fin de liste</p>
   <div id="articleList">${renderArticles(list)}</div></section>`;
 }else{
  const fallback=datedOlder.slice(0,3);
  const content=datedToday.length?renderArticles(datedToday):`<div class="today-empty glass"><strong>Aucune nouvelle publication aujourd’hui.</strong><span>Voici les 3 dernières trouvailles datées.</span></div><h2 class="recent-title">🕘 Dernières trouvailles</h2>${renderArticles(fallback,{empty:"Aucune publication datée récente."})}`;
  app.innerHTML=`<section class="panel glass"><h1 class="section-title">📰 Aujourd’hui</h1>
   <div class="toolbar"><button class="action blue" id="refresh">↻ Actualiser les trouvailles</button><button class="action green" id="add">＋ Ajouter un article</button></div>
   <p class="muted">${datedToday.length} publication(s) datée(s) d’aujourd’hui</p><div id="articleList">${content}</div></section>`;
 }
 $("#refresh").onclick=async()=>{await syncCollectedNews(true);showArticles(archive)};
 $("#add").onclick=showAddArticle;
}
function showSearch(initial=""){
 setScene("search");
 app.innerHTML=`<section class="panel glass"><h1 class="section-title">🔎 Recherche</h1><p>Cherchez dans les trouvailles collectées.</p>
 <div class="stack"><input id="q" placeholder="Mot-clé" value="${esc(initial)}"><select id="src"><option>Toutes les sources</option>${SOURCES.map(s=>`<option>${esc(s[0])}</option>`).join("")}</select>
 <button class="action green" id="local">🔎 Rechercher les trouvailles</button><button class="action blue" id="web">↻ Actualiser les trouvailles</button></div>
 <p id="searchStatus" class="muted"></p><div id="results"></div></section>`;
 const run=()=>{const q=$("#q").value.trim(),src=$("#src").value;if(!q)return toast("Saisissez un mot-clé");const list=articles().filter(a=>clientRelevant(a)&&termMatches(a,q)&&(src==="Toutes les sources"||a.source===src)).sort(sortNewest);$("#searchStatus").textContent=`${list.length} résultat(s)`;$("#results").innerHTML=renderArticles(list)};
 $("#local").onclick=run;$("#web").onclick=async()=>{await syncCollectedNews(true);run()};if(initial)run();
}
function showSources(){
 setScene("sources");
 app.innerHTML=`<section class="panel glass"><h1 class="section-title">🔗 Les 12 sources</h1><p>Touchez une source pour ouvrir son site officiel ou spécialisé.</p>${SOURCES.map(s=>`<div class="card source glass"><div><b>${esc(s[0])}</b><br><span class="badge">${esc(s[3])}</span></div><a href="${s[1]}" target="_blank" rel="noopener">Ouvrir ↗</a></div>`).join("")}</section>`;
}
function matchingFavoriteArticles(favList=favorites()){if(!favList.length)return [];return articles().filter(a=>clientRelevant(a)&&favList.some(t=>termMatches(a,t))).sort(sortNewest)}
function downloadFavorites(){const fav=favorites();const payload={app:"VeilleJurSoc",type:"favorites",version:1,exportedAt:new Date().toISOString(),favorites:fav};const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json;charset=utf-8"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`VeilleJurSoc-favoris-${new Date().toISOString().slice(0,10)}.json`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),500);toast(`${fav.length} favori(s) exporté(s)`)}
function importFavoritesFile(file){if(!file)return;const reader=new FileReader();reader.onload=()=>{try{const data=JSON.parse(String(reader.result||""));const incoming=Array.isArray(data)?data:data?.favorites;if(!Array.isArray(incoming))throw new Error("format");const cleaned=incoming.map(x=>String(x??"").trim()).filter(Boolean).slice(0,200);if(!cleaned.length)throw new Error("empty");const merged=[...favorites()];cleaned.forEach(x=>{if(!merged.some(f=>norm(f)===norm(x)))merged.push(x)});setJSON("vjs_favorites",merged);toast(`${cleaned.length} favori(s) importé(s)`);showFavorites()}catch(e){toast("Fichier de favoris non reconnu")}};reader.readAsText(file,"utf-8")}
function showFavorites(){
 setScene("favorites");
 const fav=favorites(),matches=matchingFavoriteArticles(fav);
 app.innerHTML=`<section class="panel glass"><h1 class="section-title">★ Mes sujets favoris</h1><p>Ajoutez vos thèmes personnels. Les résultats sont recalculés après chaque synchronisation.</p>
 <div class="card glass"><h3>Mes mots-clés favoris</h3><div id="favList">${fav.length?fav.map((f,i)=>`<div class="favrow favitem"><b>${esc(f)}</b><button class="danger" data-i="${i}">Supprimer</button></div>`).join(""):'<div class="empty compact">Aucun sujet favori.</div>'}</div><div class="searchrow fav-add"><input id="newFav" placeholder="Ex. PS, PMSS, DSN"><button class="action green" id="addFav">＋ Ajouter</button></div></div>
 <div class="toolbar"><button class="action blue" id="refreshFav">↻ Actualiser les trouvailles</button><button class="action blue" id="exportFav">⬇ Exporter</button><button class="action purple" id="importFav">⬆ Importer</button></div><input id="favFile" type="file" accept="application/json,.json" hidden>
 <h2 class="fav-results-title">📰 Trouvailles correspondant à mes favoris</h2><p class="muted">${matches.length} trouvaille(s) correspondant à ${fav.length} sujet(s).</p><div id="favoriteResults">${renderArticles(matches)}</div></section>`;
 document.querySelectorAll("[data-i]").forEach(b=>b.onclick=()=>{fav.splice(+b.dataset.i,1);setJSON("vjs_favorites",fav);showFavorites()});
 $("#addFav").onclick=()=>{const x=$("#newFav").value.trim();if(!x)return toast("Saisissez un sujet favori");if(fav.some(f=>norm(f)===norm(x)))return toast("Ce sujet est déjà dans vos favoris");fav.push(x);setJSON("vjs_favorites",fav);showFavorites()};
 $("#newFav").onkeydown=e=>{if(e.key==="Enter")$("#addFav").click()};
 $("#refreshFav").onclick=async()=>{await syncCollectedNews(true);showFavorites()};$("#exportFav").onclick=downloadFavorites;$("#importFav").onclick=()=>$("#favFile").click();$("#favFile").onchange=e=>importFavoritesFile(e.target.files?.[0]);
}
function showAddArticle(){
 setScene("search");
 app.innerHTML=`<section class="panel glass"><h1 class="section-title">＋ Ajouter une trouvaille</h1><div class="stack"><input id="aTitle" placeholder="Titre"><input id="aUrl" type="url" placeholder="https://…"><select id="aSource">${SOURCES.map(s=>`<option>${esc(s[0])}</option>`).join("")}</select><textarea id="aSummary" rows="5" placeholder="Résumé"></textarea><button class="action green" id="saveArticle">Enregistrer</button></div></section>`;
 $("#saveArticle").onclick=()=>{const title=$("#aTitle").value.trim(),url=$("#aUrl").value.trim();if(!title||!/^https?:\/\//i.test(url))return toast("Titre et URL valide obligatoires");const src=SOURCES.find(s=>s[0]===$("#aSource").value),all=articles();if(all.some(a=>a.url===url))return toast("Cet article est déjà enregistré");all.push({id:Date.now(),manual:true,title,url,source:src[0],sourceKind:src[3],summary:$("#aSummary").value.trim(),publishedAt:Date.now(),discoveredAt:Date.now(),topics:[]});setJSON("vjs_articles",all);toast("Trouvaille enregistrée");showArticles(false)};
}
function showThanks(){
 setScene("thanks");
 app.innerHTML=`<section class="thanks-poster">
   <img class="perfection-poster" src="assets/perfection.jpg" alt="Passer à côté d’une gestionnaire de paie, c’est frôler la perfection">
   <div class="thanks-copy">
     <p>Un grand merci à<br><b>Aurore, Chloé, Gaëlle, Tess et Thomas</b><br>pour tous les bons moments partagés pendant notre formation.</p>
     <p>Un grand merci également à<br><b>Damien et Sylvie</b>,<br>pour leur accompagnement, leur patience et tout ce qu’ils nous ont transmis.</p>
     <img class="legion-flame" src="assets/legion_flame.png" alt="Flamme de la Légion étrangère">
   </div>
 </section>`;
}
$("#homeBtn").onclick=showHome;$("#thanksBtn").onclick=showThanks;
$("#navHome").onclick=showHome;
$("#navToday").onclick=async()=>{await syncCollectedNews(false);showArticles(false)};
$("#navArchives").onclick=async()=>{await syncCollectedNews(false);showArticles(true)};
$("#navFavorites").onclick=async()=>{await syncCollectedNews(false);showFavorites()};
$("#navSources").onclick=showSources;
if("serviceWorker" in navigator)window.addEventListener("load",async()=>{try{const reg=await navigator.serviceWorker.register("./sw.js?v=47");await reg.update()}catch(e){console.warn("Service worker",e)}});
showHome();
