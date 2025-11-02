# Guide de débogage détaillé

Ce guide explique comment utiliser le débogueur dans Cursor/VS Code pour ce projet.

## Prérequis : Environnement virtuel Python

Avant de commencer le débogage, assurez-vous d'avoir créé et activé l'environnement virtuel Python :

```bash
# Créer l'environnement virtuel
python -m venv .venv  # ou python3 -m venv .venv sur Linux/Mac

# Activer l'environnement virtuel
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Installer les dépendances
pip install -r backend/requirements.txt
```

**Important** : L'interpréteur Python dans Cursor/VS Code doit pointer vers `.venv/Scripts/python.exe` (Windows) ou `.venv/bin/python` (Linux/Mac). Cursor devrait détecter automatiquement le venv, mais vous pouvez aussi le sélectionner manuellement avec `Ctrl+Shift+P` > "Python: Select Interpreter".

## Configuration des débogueurs

### Backend Python (Flask)

Le backend utilise `debugpy` pour permettre le débogage depuis Cursor/VS Code.

#### Méthode 1 : Launch (Recommandé)

1. Ouvrez le panneau de debug (`Ctrl+Shift+D`)
2. Sélectionnez "Python: Flask (Backend)"
3. Appuyez sur `F5` ou cliquez sur "Start Debugging"

Cette méthode lance Flask directement avec le débogueur intégré. **Aucune modification du code n'est nécessaire** - debugpy s'injecte automatiquement grâce à la configuration `launch`.

#### Méthode 2 : Attach

Cette méthode permet de se connecter à un processus Flask déjà en cours d'exécution :

1. **Modifiez `backend/app.py`** pour ajouter debugpy avant de démarrer Flask :
   ```python
   import debugpy
   debugpy.listen(("0.0.0.0", 5678))
   app.run(host='0.0.0.0', port=5000, debug=True)
   ```
2. Démarrez Flask manuellement : `python backend/app.py`
3. Dans Cursor, sélectionnez "Python: Flask (Attach)"
4. Appuyez sur `F5`

**Note** : Le mode "Launch" est généralement préférable car il ne nécessite aucune modification du code.

#### Utilisation des breakpoints

Placez des breakpoints dans `backend/app.py` :

- Cliquez dans la marge à gauche du numéro de ligne
- Un point rouge apparaît indiquant un breakpoint actif
- Le code s'arrêtera à cet endroit lors de l'exécution

### Frontend Vue.js

Le frontend utilise les DevTools du navigateur pour le débogage.

#### Configuration Chrome

1. Ouvrez le panneau de debug
2. Sélectionnez "Vue.js: Chrome"
3. Appuyez sur `F5`
4. Le serveur de développement Vue.js démarre automatiquement (`npm run serve`)
5. Chrome s'ouvre automatiquement avec le débogueur connecté une fois le serveur prêt

#### Configuration Edge

Même processus mais sélectionnez "Vue.js: Edge" à la place. Le serveur démarre également automatiquement.

#### Utilisation des breakpoints

Placez des breakpoints dans vos fichiers Vue.js :

- `frontend/src/App.vue` - Dans les sections `<script>`
- `frontend/src/main.js` - Point d'entrée de l'application

#### Debug dans le navigateur

Vous pouvez aussi :

- Ouvrir les DevTools manuellement (`F12`)
- Utiliser `console.log()` pour le debug
- Utiliser le debugger JavaScript : `debugger;`

## Debug combiné (Full Stack)

Pour déboguer le backend et le frontend simultanément :

1. Sélectionnez "Full Stack Debug" dans le panneau de debug
2. Appuyez sur `F5`
3. Les deux débogueurs démarrent en parallèle

Cette configuration lance automatiquement :

- Le backend Flask avec debugpy
- Chrome avec le débogueur connecté au frontend Vue.js

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

1. Placez un breakpoint dans `backend/app.py` dans la fonction `hello()`
2. Lancez "Python: Flask (Backend)"
3. Dans le frontend, cliquez sur le bouton "Appeler le Backend"
4. L'exécution s'arrête au breakpoint
5. Inspectez `request` pour voir les données de la requête

### Debug d'un composant Vue

1. Placez un breakpoint dans `frontend/src/App.vue` dans la méthode `fetchHello()`
2. Lancez "Vue.js: Chrome"
3. Cliquez sur le bouton dans l'interface
4. L'exécution s'arrête au breakpoint
5. Inspectez `this.message` et `this.loading`

### Debug d'une erreur

Si vous rencontrez une erreur :

1. Activez "Break on exceptions" dans les options de debug
2. L'exécution s'arrêtera automatiquement sur les exceptions
3. Inspectez la pile d'appels pour comprendre l'origine

## Configuration avancée

### Modifier le port de debug

Par défaut, debugpy écoute sur le port 5678. Pour le modifier :

Dans `backend/app.py` (optionnel, pour le mode attach uniquement) :

```python
debugpy.listen(("0.0.0.0", 5679))  # Port différent
```

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

   Ou utilisez le script fourni : `kill_debug_port.bat`

2. **Utiliser un port alternatif** :

   - Sélectionnez la configuration "Python: Flask (Backend - Port Alternatif)" dans le panneau de debug
   - Cette configuration utilise le port 5679 au lieu de 5678
   - Assurez-vous de mettre à jour aussi la configuration "Attach" si vous l'utilisez

3. **Modifier le port manuellement** :

   - Dans `.vscode/launch.json`, modifiez le port dans la section `connect` ou `env.DEBUGPY_PORT`
   - Ou définissez la variable d'environnement `DEBUGPY_PORT=5679` avant de lancer le debug

4. **Redémarrer Cursor/VS Code** : Fermez complètement l'IDE pour libérer les ports

### Les breakpoints ne sont pas atteints

- Vérifiez que le code est bien exécuté
- Vérifiez que les breakpoints sont sur des lignes exécutables
- Pour Python, vérifiez `"justMyCode": false` si vous voulez debugger le code des dépendances

### Le débogueur Vue.js ne fonctionne pas

- Assurez-vous que le serveur de développement est démarré (`npm run serve`)
- Vérifiez que les source maps sont activées dans `vue.config.js`
- Vérifiez que le port 8080 est accessible

### Erreur de connexion au débogueur

- Vérifiez que le port 5678 n'est pas utilisé par un autre processus
- Vérifiez que les règles de pare-feu autorisent les connexions
