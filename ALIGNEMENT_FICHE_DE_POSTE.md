# Alignement avec la fiche de poste

## Résumé
Ce POC démontre une architecture événementielle complète (Kafka), des workers ETL temps réel, un ESB hybride (Kafka + Talend documenté) et une logique BI via un data warehouse et des KPIs.

## Correspondance des exigences

### 1) Renfort junior transverse (Python / Java / .Net)
- Implémentation principale en Python (workers, ETL, tests).
- Architecture agnostique : les workers peuvent être réécrits en Java ou .Net (mêmes topics Kafka, mêmes schémas DB).

### 2) Workers event-driven / IO
- Kafka comme bus d’événements, 5 topics.
- 3 workers spécialisés :
  - UserETLWorker (transform + load)
  - OrderValidator (validation métier + routing)
  - OrderFactBuilder (data warehouse)

### 3) Mise en place Kafka / diffusion data / événements
- Docker Compose pour Kafka + Zookeeper + PostgreSQL.
- Producer simulant 100 événements et diffusion via topics.

### 4) Structuration ESB (Talend) + stabilité
- Documentation complète avec approche ESB hybride (Kafka + Talend) et alternatives.
- Découplage complet, gestion des erreurs et files d’événements.

### 5) BI (bonus)
- Data warehouse (fact_orders + users)
- KPIs : Orders/day, Revenue/day, Rejection rate

## Ce qui est livré
- Code complet (producer + 3 workers)
- Schéma DB + vues analytiques
- Dashboard KPI
- Scripts d’exécution et tests end-to-end
- Documentation technique et fonctionnelle

## Commande unique de démonstration
```powershell
.\start.ps1
```
Cette commande démarre l’infrastructure, installe les dépendances, lance les workers, attend l’ingestion et exécute le test final.

## Points forts pour l’équipe
- Démonstration claire d’architecture événementielle
- Pipeline ETL temps réel opérationnel
- Base pour intégrer d’autres technos (Java/.Net)
- Orientation data + BI
