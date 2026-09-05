const CACHE="veillejursoc-v4-pwa-1";
const ASSETS=["./","./index.html","./styles.css","./app.js","./manifest.webmanifest",
"./assets/icon-192.png","./assets/icon-512.png","./assets/emu_home_hero.png","./assets/emu_news_hero.png",
"./assets/emu_search_hero.png","./assets/emu_favorites_hero.png","./assets/perfection.jpg"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{if(e.request.method!=="GET")return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(x=>{if(new URL(e.request.url).origin===location.origin){let c=x.clone();caches.open(CACHE).then(k=>k.put(e.request,c))}return x}).catch(()=>caches.match("./index.html"))))});
