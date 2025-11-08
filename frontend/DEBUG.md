# Guide de débogage du Frontend

Ce guide explique comment déboguer le frontend Vue.js dans Cursor/VS Code.

## Configuration des débogueurs

### Frontend Vue.js

Le frontend utilise les DevTools du navigateur pour le débogage.

#### Configuration Chrome

1. Ouvrez le panneau de debug (`Ctrl+Shift+D`)
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
- `frontend/src/views/*.vue` - Dans les vues
- `frontend/src/components/*.vue` - Dans les composants

#### Debug dans le navigateur

Vous pouvez aussi :

- Ouvrir les DevTools manuellement (`F12`)
- Utiliser `console.log()` pour le debug
- Utiliser le debugger JavaScript : `debugger;`

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
- Variables du composant Vue (data, computed, props)
- Variables globales

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

### Debug d'un composant Vue

1. Placez un breakpoint dans `frontend/src/views/Regions.vue` dans la méthode `fetchRegions()`
2. Lancez "Vue.js: Chrome"
3. Naviguez vers la page des régions
4. L'exécution s'arrête au breakpoint
5. Inspectez `this.regions` et `this.loading`

### Debug d'un appel API

1. Placez un breakpoint dans `frontend/src/services/api.js` dans la méthode `getRegions()`
2. Lancez le débogueur
3. Faites une action qui déclenche l'appel API
4. Inspectez les paramètres et la réponse

### Debug d'une erreur

Si vous rencontrez une erreur :

1. Activez "Break on exceptions" dans les options de debug
2. L'exécution s'arrêtera automatiquement sur les exceptions
3. Inspectez la pile d'appels pour comprendre l'origine

## Debug combiné (Full Stack)

Pour déboguer le backend et le frontend simultanément :

1. Sélectionnez "Full Stack Debug" dans le panneau de debug
2. Appuyez sur `F5`
3. Les deux débogueurs démarrent en parallèle

Cette configuration lance automatiquement :

- Le backend FastAPI avec debugpy
- Chrome avec le débogueur connecté au frontend Vue.js

## Dépannage

### Le débogueur Vue.js ne fonctionne pas

- Assurez-vous que le serveur de développement est démarré (`npm run serve`)
- Vérifiez que les source maps sont activées dans `vue.config.js`
- Vérifiez que le port 8080 est accessible

### Les breakpoints ne sont pas atteints

- Vérifiez que le code est bien exécuté
- Vérifiez que les breakpoints sont sur des lignes exécutables
- Vérifiez que les source maps sont générées correctement

### Le frontend ne peut pas appeler le backend

- Vérifiez que les deux services sont démarrés
- Vérifiez que CORS est activé dans le backend
- Vérifiez que l'URL du backend est correcte dans `api.js`

### Erreur de connexion au débogueur

- Vérifiez que Chrome/Edge n'est pas déjà ouvert avec un autre débogueur
- Fermez tous les onglets de debug précédents
- Redémarrez le serveur de développement

