const CACHE="veillejursoc-v4-pwa-5";
const ASSETS=["./","./index.html","./styles.css","./app.js","./manifest.webmanifest","./assets/icon-192.png","./assets/icon-512.png","./assets/emu_home_hero.png","./assets/emu_news_hero.png","./assets/emu_search_hero.png","./assets/emu_favorites_hero.png","./assets/perfection.jpg"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{
 if(e.request.method!=="GET")return;
 const url=new URL(e.request.url);
 if(url.pathname.endsWith("/app.js")||url.pathname.endsWith("/index.html")||url.pathname.endsWith("/")){
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)));return;
 }
 if(url.pathname.endsWith("/data/news.json")){e.respondWith(fetch(e.request,{cache:"no-store"}));return;}
 e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request).then(r=>{if(url.origin===location.origin){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}return r}).catch(()=>caches.match("./index.html"))));
});
