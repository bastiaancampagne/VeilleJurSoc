# VeilleJurSoc PWA v4

Conversion PWA du projet Android VeilleJurSoc v4.

## Fonctions reprises
- Accueil et identité visuelle avec les illustrations d'émeu du projet Android.
- Aujourd'hui et Archives, tri du plus récent au plus ancien.
- Recherche locale dans les articles enregistrés.
- Recherche ciblée sur les 12 domaines de référence.
- 12 sources : BOSS, Légifrance, URSSAF, Net-entreprises, Ministère du Travail,
  Service-Public Pro, Assurance Maladie, France Travail, Agirc-Arrco,
  Légisocial, RF Paye et Éditions Tissot.
- Sujets favoris persistants.
- Page Remerciements.
- Installation comme application PWA.
- Cache Service Worker pour l'interface hors connexion.
- Données locales persistantes via localStorage.
- Ajout manuel d'une trouvaille/article.

## Différence importante avec l'APK Android
L'APK peut lancer son propre scraper Jsoup en tâche de fond. Une PWA exécutée uniquement dans
le navigateur ne peut pas aspirer librement les 12 sites à cause des politiques CORS et ne peut
pas garantir une exécution quotidienne à 08h00 lorsqu'elle est fermée.

Dans cette version sans serveur, « Rechercher les nouveautés » ouvre donc une recherche web
ciblée sur les 12 domaines. Pour retrouver exactement l'actualisation automatique de l'APK,
il faut ajouter un petit backend/proxy (ou une fonction serverless) qui effectue la collecte,
puis expose les résultats à la PWA.

## Test local
Un Service Worker exige HTTP/HTTPS. Ne pas ouvrir simplement index.html en file://.

Exemples :
- VS Code : extension Live Server
- Python : `python -m http.server 8080`
Puis ouvrir `http://localhost:8080`.

## Installation
Une fois déployée en HTTPS, ouvrir la PWA dans Chrome/Edge puis choisir
« Installer l'application » / « Ajouter à l'écran d'accueil ».


## Nouveautés v4.2 — Mes sujets favoris

- La page « Mes sujets favoris » affiche directement les articles correspondant à au moins un favori.
- Les résultats sont triés du plus récent au plus ancien.
- Ajout/suppression des favoris avec détection des doublons.
- Export des favoris dans un fichier JSON.
- Import de ce fichier sur un autre appareil.
- Les favoris importés sont fusionnés sans doublons avec ceux déjà présents.
- Les favoris restent personnels à chaque appareil et ne modifient pas GitHub.

## v4.8
La page Remerciements reprend le visuel « Frôler la perfection », avec le texte original et la flamme de la Légion étrangère sous le message. La signature Bastiaan (31) TM reste dans le pied de page de l'application.


## v4.9
La flamme de la Légion étrangère de la page Remerciements a été remplacée par l’image exacte fournie par l’utilisateur.


## v4.10
Page Remerciements mise à jour avec l’insigne circulaire exact fourni, fond extérieur transparent et sans mention LEGIO PATRIA NOSTRA. Maquette complète incluse dans `maquette/VeilleJurSoc_maquette_v4_10.png`.
