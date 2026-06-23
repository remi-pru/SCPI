# Visualiseur d'allocation SCPI

Application web pour visualiser une allocation de SCPI en détail et synthétiser
le portefeuille selon des pondérations variables.

## Contenu

| Fichier | Rôle |
|---|---|
| `Allocation SCPI.dc.html` | Application principale (source, modifiable) |
| `support.js` | Moteur d'exécution requis par l'application |
| `Allocation-SCPI-standalone.html` | Version autonome : **se lance par simple double-clic**, fonctionne hors-ligne |

## Lancer l'application

### Option 1 — le plus simple
Ouvrez `Allocation-SCPI-standalone.html` directement dans votre navigateur
(double-clic). Aucune installation requise, fonctionne sans connexion.

### Option 2 — dans VS Code (pour modifier)
1. Ouvrez ce dossier dans VS Code (`Fichier ▸ Ouvrir le dossier…`).
2. Installez l'extension **Live Server** (Ritwick Dey).
3. Clic droit sur `Allocation SCPI.dc.html` ▸ **Open with Live Server**.

> `Allocation SCPI.dc.html` et `support.js` doivent rester dans le même dossier.

## Fonctionnalités

- **Page Synthèse** : curseurs de pondération par SCPI, montant à investir,
  donut de répartition, indicateurs moyens pondérés (rendement, PGA, TOF,
  décote, LTV), répartitions géographique et sectorielle agrégées, revenu
  annuel et mensuel estimé.
- **Une page par SCPI** : tous les indicateurs clés, répartitions et analyse
  détaillée (6 SCPI : ActivImmo, Cœur de Régions, Cristal Life, Cristal Rente,
  Sofidynamic, Alta Convictions).
- Bascule **mode clair / sombre**.

Données : exercice 2025 (source : synthèse de l'allocation SCPI 2026).
