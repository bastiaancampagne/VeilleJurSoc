VeilleJurSoc - collecteur v4.4

À remplacer dans GitHub :
- scripts/scrape.py : OUI, c'est la mise à jour principale.
- data/news.json : OPTIONNEL. Ne le remplacez pas si vous souhaitez conserver les trouvailles déjà collectées.

Le nouveau scrape.py nettoie automatiquement les anciennes entrées lors de sa prochaine exécution.
Il exclut davantage les formations, podcasts, pages commerciales et pages de navigation,
privilégie les vraies pages d'actualité, conserve les dates publiées valides et ajoute un champ "topics".
