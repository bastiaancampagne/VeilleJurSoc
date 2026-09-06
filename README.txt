VeilleJurSoc collecteur v4.5

À remplacer dans GitHub :
  scripts/scrape.py

Ne remplacez pas data/news.json.

Améliorations :
- fenêtre d'actualité de 90 jours ;
- suppression des anciennes pages documentaires Net-entreprises ;
- correction du thème Rémunération pour éviter la confusion payer/paye ;
- 3 tentatives réseau pour les erreurs temporaires ;
- conservation du filtrage formations/podcasts/pages commerciales ;
- conservation des topics.

Après remplacement :
1. Commit changes
2. Vérifier FRESHNESS_DAYS = 90 dans scripts/scrape.py
3. Actions > Actualiser VeilleJurSoc > Run workflow
4. Vérifier data/news.json
