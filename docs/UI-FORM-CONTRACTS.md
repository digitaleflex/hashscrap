# Contrats des formulaires UI

Ce document fait le lien entre les champs du prototype `prototypes/hashscrap-ui/index.html` et les interfaces réellement présentes dans le dépôt. Le prototype reste statique : il ne lance aucune requête réseau, ne crée aucun enregistrement et n’écrit aucun fichier.

## Source

Le formulaire de préparation de source reflète `hashscrap.config.Source` dans `hashscrap/config.py` :

- `id`, `name`, `type`, `base_url`, `enabled`, `allowed_hosts`
- `AppConfig.limits.timeout_seconds`, `AppConfig.limits.concurrency`, `AppConfig.limits.requests_per_second`, `AppConfig.limits.max_depth`, `AppConfig.limits.max_pages`, `AppConfig.limits.max_response_bytes` (limites globales)
- `Source.limits.timeout_seconds`, `Source.limits.concurrency`, `Source.limits.requests_per_second`, `Source.limits.max_depth`, `Source.limits.max_pages`, `Source.limits.max_response_bytes` (limites propres à la source)

`type` est limité à `website`. `allowed_hosts` doit contenir uniquement des noms d’hôtes, et l’hôte de `base_url` doit être inclus dans cette liste. Les limites d’une source ne peuvent pas dépasser les limites globales de `AppConfig`. Le formulaire n’enregistre pas ces valeurs : il rappelle qu’elles doivent être reportées dans le fichier JSON de configuration.

Le contrat HTTP actuel expose seulement `GET /api/v1/sources`. Il n’existe pas d’endpoint de création/modification de source dans `hashscrap/api.py`.

## Collecte

Le formulaire de préparation de commande reflète les options de `hashscrap run` et `hashscrap crawl` dans `hashscrap/cli.py` :

- `--config` : chemin vers la configuration JSON validée
- `--source` : identifiant d’une source activée dans cette configuration
- `--url` : option répétable pour fournir des URL de départ explicites ; en son absence, le moteur utilise `source.base_url`

Le prototype ne déclenche pas la commande. L’API HTTP actuelle n’expose aucun endpoint de lancement de collecte ; `GET /api/v1/runs` est en lecture seule.

## Rapports et export

Les champs du prototype correspondent aux options de `hashscrap report` :

- `--format` : `markdown` ou `json`
- `--investigation-id`
- `--title`
- `--scope`
- `--source`
- `--output`
- `--max-observations`
- `--max-relationships`

Le moteur produit un rapport à partir des preuves persistées. Le prototype ne génère pas le rapport et ne crée pas le fichier.

## Actions laissées indisponibles

Aucun formulaire fictif n’est proposé pour les actions suivantes, car le backend ne fournit pas de contrat correspondant :

- création d’une investigation (aucun modèle/endpoint d’investigation exposé)
- aperçu de rapport (aucun endpoint d’aperçu)
- modification des paramètres (aucun endpoint de mise à jour)

Ces actions restent visibles dans le prototype mais sont désactivées. Elles ne doivent pas être présentées comme des fonctions opérationnelles.

## Interface React active

L’application React active reste alignée sur les endpoints réellement exposés : elle lit les sources, collectes, documents et observations. Les boutons de création/lancement restent désactivés tant qu’un contrat backend de mutation n’existe pas. Ne pas ajouter de formulaire qui envoie des données vers une route supposée.
