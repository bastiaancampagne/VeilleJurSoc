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
const DEFAULT_FAV=["DSN","SMIC","RGDU","IJSS","Rupture conventionnelle","Net social"];
const $=s=>document.querySelector(s), app=$("#app");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const norm=s=>String(s??"").normalize("NFD").replace(/\p{Diacritic}/gu,"").toLowerCase();
const getJSON=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
const setJSON=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
const favorites=()=>getJSON("vjs_favorites",DEFAULT_FAV);
const articles=()=>getJSON("vjs_articles",[]);
const toast=m=>{let t=$("#toast");t.textContent=m;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2600)};
const hero=(name,small=false)=>`<img class="hero ${small?"small":""}" src="assets/${name}" alt="Illustration humoristique de l’émeu VeilleJurSoc">`;
const todayStart=()=>{let d=new Date();d.setHours(0,0,0,0);return +d};
const stamp=t=>t?new Intl.DateTimeFormat("fr-FR",{dateStyle:"short",timeStyle:"short"}).format(new Date(t)):"Date de publication non indiquée";
function sortNewest(a,b){return (b.publishedAt||b.discoveredAt||0)-(a.publishedAt||a.discoveredAt||0)}
function isFav(a){let n=norm(`${a.title} ${a.summary}`);return favorites().some(x=>n.includes(norm(x)))}
function renderArticles(list){
 if(!list.length)return `<div class="empty">Aucune trouvaille enregistrée.</div>`;
 return list.sort(sortNewest).map(a=>`<article class="card" data-url="${esc(a.url)}">
   <h3>${isFav(a)?'<span class="star">★ </span>':''}${esc(a.title)}</h3>
   <div class="meta">${esc(a.source)} • ${esc(a.sourceKind)} • ${stamp(a.publishedAt)}</div>
   <p class="summary">${esc(a.summary||"")}</p>
   <a href="${esc(a.url)}" target="_blank" rel="noopener">Ouvrir l’article ↗</a>
 </article>`).join("");
}
function showHome(){
 app.innerHTML=`<section>${hero("emu_home_hero.png")}<h1 class="title">VeilleJurSoc</h1>
 <p class="subtitle">Votre veille juridique et sociale pour les professionnels de la paie</p>
 <p class="gag">🧮 L’émeu RH surveille la paie… sans se prendre la tête ! 🔥</p>
 <div class="stack">
  <div class="searchrow"><input id="homeSearch" placeholder="Rechercher : DSN, SMIC, IJSS, RGDU…"><button class="action green" id="searchGo">🔎 Recherche</button></div>
  <button class="action blue" id="today">📰 Aujourd’hui</button>
  <button class="action green" id="archives">🗄️ Archives</button>
  <button class="action gold" id="favorites">★ Mes sujets favoris</button>
  <button class="action purple" id="sources">🔗 Les 12 sources</button>
 </div>
 <p class="muted">Dernière mise à jour locale : ${esc(localStorage.getItem("vjs_last_refresh")||"jamais")}</p>
 <p class="note"><b>Version PWA :</b> les pages externes ne peuvent pas être aspirées directement par le navigateur si leurs serveurs bloquent CORS. La recherche ciblée ouvre donc une requête sur les 12 domaines. Les articles ajoutés/importés restent enregistrés localement et disponibles hors connexion.</p>
 </section>`;
 $("#searchGo").onclick=()=>showSearch($("#homeSearch").value.trim());
 $("#homeSearch").onkeydown=e=>{if(e.key==="Enter")showSearch(e.target.value.trim())};
 $("#today").onclick=()=>showArticles(false);$("#archives").onclick=()=>showArticles(true);
 $("#favorites").onclick=showFavorites;$("#sources").onclick=showSources;
}
function showArticles(archive){
 let start=todayStart(), list=articles().filter(a=>archive?((a.publishedAt>0?a.publishedAt:a.discoveredAt)<start):((a.publishedAt>0?a.publishedAt:a.discoveredAt)>=start));
 app.innerHTML=`<h1 class="section-title">${archive?"🗄️ Archives":"📰 Aujourd’hui"}</h1>${hero("emu_news_hero.png",true)}
 <div class="toolbar"><button class="action blue" id="refresh">🌐 Rechercher les nouveautés</button><button class="action green" id="add">＋ Ajouter un article</button></div>
 <p class="muted">${list.length} trouvaille(s) • les plus récentes en haut</p><div id="articleList">${renderArticles(list)}</div>`;
 $("#refresh").onclick=()=>openWebSearch(""); $("#add").onclick=showAddArticle;
}
function showSearch(initial=""){
 app.innerHTML=`<h1 class="section-title">🔎 Recherche</h1>${hero("emu_search_hero.png",true)}
 <p>Cherchez dans les contenus enregistrés ou lancez une recherche ciblée sur vos 12 sites de référence.</p>
 <div class="stack"><input id="q" placeholder="Mot-clé" value="${esc(initial)}"><select id="src"><option>Toutes les sources</option>${SOURCES.map(s=>`<option>${esc(s[0])}</option>`).join("")}</select>
 <button class="action green" id="local">Rechercher dans l’application</button><button class="action blue" id="web">🌐 Rechercher aussi sur les 12 sources</button></div>
 <p id="searchStatus" class="muted"></p><div id="results"></div>`;
 const run=()=>{let q=$("#q").value.trim(),src=$("#src").value;if(!q)return toast("Saisissez un mot-clé");
   let nq=norm(q),list=articles().filter(a=>(norm(`${a.title} ${a.summary} ${a.source}`).includes(nq))&&(src==="Toutes les sources"||a.source===src));
   $("#searchStatus").textContent=`${list.length} résultat(s) dans Aujourd’hui + Archives`;$("#results").innerHTML=renderArticles(list)};
 $("#local").onclick=run;$("#web").onclick=()=>openWebSearch($("#q").value.trim());
 if(initial)run();
}
function openWebSearch(term){
 let sites="("+SOURCES.map(s=>`site:${s[2]}`).join(" OR ")+") "+term;
 window.open("https://www.google.com/search?q="+encodeURIComponent(sites),"_blank","noopener");
 localStorage.setItem("vjs_last_refresh",new Intl.DateTimeFormat("fr-FR",{dateStyle:"short",timeStyle:"short"}).format(new Date()));
}
function showSources(){
 app.innerHTML=`<h1 class="section-title">🔗 Les 12 sources</h1>${hero("emu_news_hero.png",true)}
 <p>Touchez une source pour ouvrir son site officiel ou spécialisé.</p>
 ${SOURCES.map(s=>`<div class="card source"><div><b>${esc(s[0])}</b><br><span class="badge">${esc(s[3])}</span></div><a href="${s[1]}" target="_blank" rel="noopener">Ouvrir ↗</a></div>`).join("")}`;
}
function showFavorites(){
 let fav=favorites();
 app.innerHTML=`<h1 class="section-title">★ Mes sujets favoris</h1>${hero("emu_favorites_hero.png",true)}
 <p>Les articles contenant ces sujets sont signalés par ★ dans Aujourd’hui, Archives et Recherche.</p>
 <div id="favList">${fav.map((f,i)=>`<div class="card favrow"><b>${esc(f)}</b><button class="danger" data-i="${i}">Supprimer</button></div>`).join("")}</div>
 <div class="searchrow"><input id="newFav" placeholder="Ex. PMSS"><button class="action green" id="addFav">＋ Ajouter</button></div>`;
 document.querySelectorAll("[data-i]").forEach(b=>b.onclick=()=>{fav.splice(+b.dataset.i,1);setJSON("vjs_favorites",fav);showFavorites()});
 $("#addFav").onclick=()=>{let x=$("#newFav").value.trim();if(x&&!fav.some(f=>norm(f)===norm(x))){fav.push(x);setJSON("vjs_favorites",fav);showFavorites()}};
}
function showAddArticle(){
 app.innerHTML=`<h1 class="section-title">＋ Ajouter une trouvaille</h1>
 <div class="stack"><input id="aTitle" placeholder="Titre"><input id="aUrl" type="url" placeholder="https://…">
 <select id="aSource">${SOURCES.map(s=>`<option>${esc(s[0])}</option>`).join("")}</select>
 <textarea id="aSummary" rows="5" placeholder="Résumé" style="width:100%;padding:.9rem;border-radius:12px;border:1px solid #aeb8c4"></textarea>
 <button class="action green" id="saveArticle">Enregistrer</button></div>`;
 $("#saveArticle").onclick=()=>{let title=$("#aTitle").value.trim(),url=$("#aUrl").value.trim();if(!title||!/^https?:\/\//i.test(url))return toast("Titre et URL valide obligatoires");
   let src=SOURCES.find(s=>s[0]===$("#aSource").value),all=articles();if(all.some(a=>a.url===url))return toast("Cet article est déjà enregistré");
   all.push({id:Date.now(),title,url,source:src[0],sourceKind:src[3],summary:$("#aSummary").value.trim(),publishedAt:Date.now(),discoveredAt:Date.now()});
   setJSON("vjs_articles",all);localStorage.setItem("vjs_last_refresh",new Intl.DateTimeFormat("fr-FR",{dateStyle:"short",timeStyle:"short"}).format(new Date()));toast("Trouvaille enregistrée");showArticles(false)};
}
function showThanks(){
 app.innerHTML=`<section class="thanks"><img src="assets/perfection.jpg" alt="Remerciements">
 <p>Un grand merci à
<b>Aurore, Chloé, Gaëlle, Tess et Thomas</b>
pour tous les bons moments partagés pendant notre formation.

Un grand merci également à
<b>Damien et Sylvie</b>,
pour leur accompagnement, leur patience et tout ce qu’ils nous ont transmis.

🔥 Bastiaan (31) TM</p></section>`;
}
$("#homeBtn").onclick=showHome;$("#thanksBtn").onclick=showThanks;
if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));
showHome();
