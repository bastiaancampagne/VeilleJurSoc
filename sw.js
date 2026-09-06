const CACHE="veillejursoc-v4-pwa-3";

const ASSETS=[
 "./",
 "./index.html",
 "./styles.css",
 "./app.js",
 "./manifest.webmanifest",
 "./assets/icon-192.png",
 "./assets/icon-512.png",
 "./assets/emu_home_hero.png",
 "./assets/emu_news_hero.png",
 "./assets/emu_search_hero.png",
 "./assets/emu_favorites_hero.png",
 "./assets/perfection.jpg"
];

self.addEventListener("install",event=>{
 event.waitUntil(
  caches.open(CACHE)
   .then(cache=>cache.addAll(ASSETS))
   .then(()=>self.skipWaiting())
 );
});

self.addEventListener("activate",event=>{
 event.waitUntil(
  caches.keys()
   .then(keys=>Promise.all(
    keys
     .filter(key=>key!==CACHE)
     .map(key=>caches.delete(key))
   ))
   .then(()=>self.clients.claim())
 );
});

self.addEventListener("fetch",event=>{
 if(event.request.method!=="GET")return;

 const url=new URL(event.request.url);

 // app.js et index.html : toujours essayer le réseau d'abord
 if(
  url.pathname.endsWith("/app.js") ||
  url.pathname.endsWith("/index.html") ||
  url.pathname.endsWith("/")
 ){
  event.respondWith(
   fetch(event.request)
    .then(response=>{
     const copy=response.clone();
     caches.open(CACHE).then(cache=>cache.put(event.request,copy));
     return response;
    })
    .catch(()=>caches.match(event.request))
  );
  return;
 }

 // data/news.json : toujours réseau, jamais vieux cache
 if(url.pathname.endsWith("/data/news.json")){
  event.respondWith(
   fetch(event.request,{cache:"no-store"})
  );
  return;
 }

 // autres ressources : cache d'abord
 event.respondWith(
  caches.match(event.request)
   .then(cached=>{
    if(cached)return cached;

    return fetch(event.request)
     .then(response=>{
      if(url.origin===location.origin){
       const copy=response.clone();
       caches.open(CACHE).then(cache=>cache.put(event.request,copy));
      }
      return response;
     })
     .catch(()=>caches.match("./index.html"));
   })
 );
});
