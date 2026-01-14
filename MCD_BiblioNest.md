# Modèle Conceptuel de Données (MCD) - BiblioNest (Corrigé)

Voici le MCD corrigé qui fait le pont entre votre schéma original (en français) et l'implémentation réelle dans le code Python (`models.py`).

## 📊 Structure des Tables (Dictionnaire de Données)

### TABLE: Admin

| Attribut            | Type       | Description                              |
| :------------------ | :--------- | :--------------------------------------- |
| **id** (PK)         | Entier     | Identifiant unique (Remplace `id_admin`) |
| **nom**             | Texte(100) | Nom de l'administrateur                  |
| **nom_utilisateur** | Texte(50)  | Login (Unique)                           |
| **mot_de_passe**    | Texte(255) | Hash du mot de passe                     |
| **role**            | Texte(50)  | Rôle (Super Admin / Admin)               |
| **date_creation**   | DateTime   | Date de création du compte               |

### TABLE: Auteur

| Attribut            | Type       | Description                              |
| :------------------ | :--------- | :--------------------------------------- |
| **id** (PK)         | Entier     | Identifiant unique                       |
| **nom_complet**     | Texte(150) | Nom + Prénom fusionnés (pour simplifier) |
| **annee_naissance** | Entier     | Année de naissance                       |
| **nationalite**     | Texte(100) | Pays d'origine                           |

### TABLE: Categorie

| Attribut    | Type       | Description             |
| :---------- | :--------- | :---------------------- |
| **id** (PK) | Entier     | Identifiant unique      |
| **nom**     | Texte(100) | Libellé de la catégorie |

### TABLE: Livre

| Attribut               | Type       | Description                                         |
| :--------------------- | :--------- | :-------------------------------------------------- |
| **id** (PK)            | Entier     | Identifiant interne (Indispensable pour SQLAlchemy) |
| **titre**              | Texte(255) | Titre de l'ouvrage                                  |
| **id_auteur** (FK)     | Entier     | Clé étrangère vers Auteur                           |
| **id_categorie** (FK)  | Entier     | Clé étrangère vers Categorie                        |
| **isbn**               | Texte(20)  | Code ISBN (Reste unique mais n'est plus la PK)      |
| **annee_publication**  | Entier     | Année de parution                                   |
| **prix**               | Décimal    | Prix de l'ouvrage                                   |
| **exemplaires_totaux** | Entier     | Stock total possédé                                 |
| **exemplaires_dispos** | Entier     | Stock disponible pour prêt                          |
| **image_path**         | Texte(255) | Chemin de la couverture                             |

### TABLE: Membre (Lecteur)

| Attribut             | Type       | Description                               |
| :------------------- | :--------- | :---------------------------------------- |
| **id** (PK)          | Entier     | Identifiant unique (Remplace `id_membre`) |
| **prenom**           | Texte(100) | Prénom du lecteur                         |
| **nom**              | Texte(100) | Nom du lecteur                            |
| **email**            | Texte(150) | Email (Unique)                            |
| **telephone**        | Texte(20)  | Numéro de téléphone                       |
| **date_inscription** | Date       | Date d'adhésion                           |
| **statut**           | Enum       | Actif, Suspendu                           |

### TABLE: Pret

| Attribut           | Type   | Description                         |
| :----------------- | :----- | :---------------------------------- |
| **id** (PK)        | Entier | Identifiant unique                  |
| **id_livre** (FK)  | Entier | Clé étrangère vers Livre            |
| **id_membre** (FK) | Entier | Clé étrangère vers Membre           |
| **date_pret**      | Date   | Date d'emprunt                      |
| **date_echeance**  | Date   | Date de retour prévue               |
| **date_retour**    | Date   | Date de retour effective (si rendu) |
| **statut**         | Enum   | En cours, Retard, Terminé           |

### TABLE: Reservation

| Attribut             | Type   | Description                   |
| :------------------- | :----- | :---------------------------- |
| **id** (PK)          | Entier | Identifiant unique            |
| **id_livre** (FK)    | Entier | Clé étrangère vers Livre      |
| **id_membre** (FK)   | Entier | Clé étrangère vers Membre     |
| **date_reservation** | Date   | Date de la demande            |
| **date_expiration**  | Date   | Date de fin de validité       |
| **statut**           | Enum   | En attente, Terminée, Annulée |

### TABLE: Type_Penalite

| Attribut            | Type       | Description                 |
| :------------------ | :--------- | :-------------------------- |
| **id** (PK)         | Entier     | Identifiant unique          |
| **libelle**         | Texte(100) | Motif (Retard, Perte, etc.) |
| **description**     | Texte      | Explication détaillée       |
| **montant_fixe**    | Décimal    | Frais fixes éventuels       |
| **taux_journalier** | Décimal    | Montant par jour de retard  |

### TABLE: Penalite

| Attribut           | Type    | Description                         |
| :----------------- | :------ | :---------------------------------- |
| **id** (PK)        | Entier  | Identifiant unique                  |
| **id_membre** (FK) | Entier  | Clé étrangère vers Membre           |
| **id_pret** (FK)   | Entier  | Clé étrangère vers Pret (optionnel) |
| **id_type** (FK)   | Entier  | Clé étrangère vers Type_Penalite    |
| **raison**         | Texte   | Détails précis de l'incident        |
| **montant**        | Décimal | Total à régler                      |
| **date_penalite**  | Date    | Date du constat                     |
| **statut**         | Enum    | Payé, Impayé                        |

---

## 📝 Rapport de Correction

1.  **Uniformisation des clés** : Utilisation de `id` comme clé primaire pour toutes les tables (au lieu de `isbn` ou `id_admin`). C'est la norme moderne pour les bases de données SQL gérées par un ORM.
2.  **Gestion de Stock** : Ajout de `exemplaires_totaux` et `exemplaires_dispos` dans la table **Livre**. Votre schéma original n'avait qu'un booléen "disponible", ce qui ne permettait pas de gérer plusieurs copies d'un même livre.
3.  **Simplication Auteur** : Fusion du nom et prénom en `nom_complet` pour correspondre à l'interface de recherche simplifiée du site.
4.  **Extension des Pénalités** : La relation entre **Pret** et **Penalite** est devenue optionnelle, permettant de mettre une amende même sans prêt (ex: comportement inapproprié) ou sur des prêts déjà archivés.
