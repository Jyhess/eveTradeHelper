# Guide de débogage du Backend

Ce guide explique comment utiliser le débogueur dans Cursor/VS Code pour le backend Python.

## Prérequis : Environnement virtuel Python

Avant de commencer le débogage, assurez-vous d'avoir créé et activé l'environnement virtuel Python :

```bash
# Créer l'environnement virtuel
make develop

# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

**Important** : L'interpréteur Python dans Cursor/VS Code doit pointer vers `.venv/Scripts/python.exe` (Windows) ou `.venv/bin/python` (Linux/Mac). Cursor devrait détecter automatiquement le venv, mais vous pouvez aussi le sélectionner manuellement avec `Ctrl+Shift+P` > "Python: Select Interpreter".

## Configuration des débogueurs

### Backend Python (FastAPI)

Le backend utilise `debugpy` pour permettre le débogage depuis Cursor/VS Code.

#### Méthode 1 : Launch (Recommandé)

1. Ouvrez le panneau de debug (`Ctrl+Shift+D`)
2. Sélectionnez "Python: Flask (Backend)"
3. Appuyez sur `F5` ou cliquez sur "Start Debugging"

Cette méthode lance FastAPI directement avec le débogueur intégré. **Aucune modification du code n'est nécessaire** - debugpy s'injecte automatiquement grâce à la configuration `launch`.

#### Méthode 2 : Attach

Cette méthode permet de se connecter à un processus FastAPI déjà en cours d'exécution :

1. **Modifiez `backend/app.py`** pour ajouter debugpy avant de démarrer FastAPI :

   ```python
   import debugpy
   debugpy.listen(("0.0.0.0", 5678))
   app.run(host='0.0.0.0', port=5000, debug=True)
   ```

2. Démarrez FastAPI manuellement : `python backend/app.py`
3. Dans Cursor, sélectionnez "Python: Flask (Attach)"
4. Appuyez sur `F5`

**Note** : Le mode "Launch" est généralement préférable car il ne nécessite aucune modification du code.

#### Utilisation des breakpoints

Placez des breakpoints dans `backend/app.py` ou dans n'importe quel fichier Python :

- Cliquez dans la marge à gauche du numéro de ligne
- Un point rouge apparaît indiquant un breakpoint actif
- Le code s'arrêtera à cet endroit lors de l'exécution

## Commandes de debug utiles

| Commande       | Raccourci       | Description                       |
| -------------- | --------------- | --------------------------------- |
| Start/Continue | `F5`            | Démarrer ou continuer l'exécution |
| Step Over      | `F10`           | Exécuter la ligne courante        |
| Step Into      | `F11`           | Entrer dans la fonction           |
| Step Out       | `Shift+F11`     | Sortir de la fonction courante    |
| Restart        | `Ctrl+Shift+F5` | Redémarrer le débogueur           |
| Stop           | `Shift+F5`      | Arrêter le débogueur              |

## Panneaux de debug

### Variables

Affiche toutes les variables dans le scope actuel :

- Variables locales
- Variables globales
- Paramètres de fonction

### Watch

Surveillez des expressions spécifiques :

- Ajoutez des expressions à surveiller
- Les valeurs sont mises à jour en temps réel

### Call Stack

Affiche la pile d'appels (stack trace) :

- Voir d'où vient l'appel de fonction
- Naviguer entre les différents niveaux

### Breakpoints

Gérez tous vos breakpoints :

- Activer/désactiver
- Supprimer
- Voir les conditions et logpoints

## Exemples pratiques

### Debug d'une requête API

1. Placez un breakpoint dans `backend/application/region_api.py` dans la fonction `get_regions()`
2. Lancez "Python: Flask (Backend)"
3. Faites une requête HTTP vers `http://localhost:5001/api/v1/regions`
4. L'exécution s'arrête au breakpoint
5. Inspectez les variables pour voir les données de la requête

### Debug d'un service de domaine

1. Placez un breakpoint dans `backend/domain/region_service.py` dans la méthode `get_regions_with_details()`
2. Lancez le débogueur
3. Faites une requête API qui déclenche ce service
4. Inspectez les variables et la pile d'appels

### Debug d'une erreur

Si vous rencontrez une erreur :

1. Activez "Break on exceptions" dans les options de debug
2. L'exécution s'arrêtera automatiquement sur les exceptions
3. Inspectez la pile d'appels pour comprendre l'origine

## Configuration avancée

### Modifier le port de debug

Par défaut, debugpy écoute sur le port 5678. Pour le modifier :

Dans `.vscode/launch.json`, mettez à jour :

```json
"connect": {
  "host": "localhost",
  "port": 5679
}
```

### Ajouter des variables d'environnement

Dans `.vscode/launch.json`, section `env` :

```json
"env": {
  "FLASK_ENV": "development",
  "REDIS_URL": "redis://localhost:6379",
  "CUSTOM_VAR": "value"
}
```

## Dépannage

### Le débogueur Python ne démarre pas

- Vérifiez que Python est bien installé
- Vérifiez que debugpy est installé : `pip install debugpy`
- Vérifiez que l'extension Python est installée dans Cursor

### Erreur "Port déjà utilisé" (WinError 10048)

Cette erreur se produit quand le port 5678 est déjà utilisé par un autre processus (souvent une session de debug précédente).

**Solutions :**

1. **Trouver et arrêter le processus** :

   ```bash
   # Trouver le PID du processus
   netstat -ano | findstr :5678

   # Arrêter le processus (remplacer <PID> par le numéro trouvé)
   taskkill /PID <PID> /F
   ```

2. **Utiliser un port alternatif** :

   - Sélectionnez la configuration "Python: Flask (Backend - Port Alternatif)" dans le panneau de debug
   - Cette configuration utilise le port 5679 au lieu de 5678

3. **Redémarrer Cursor/VS Code** : Fermez complètement l'IDE pour libérer les ports

### Les breakpoints ne sont pas atteints

- Vérifiez que le code est bien exécuté
- Vérifiez que les breakpoints sont sur des lignes exécutables
- Pour Python, vérifiez `"justMyCode": false` si vous voulez debugger le code des dépendances

### Erreur de connexion au débogueur

- Vérifiez que le port 5678 n'est pas utilisé par un autre processus
- Vérifiez que les règles de pare-feu autorisent les connexions
