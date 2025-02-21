# Mockup Generator GitHub Action

Ce projet permet de générer automatiquement des mockups d'iPhone à partir d'images partagées dans les issues GitHub.

## Comment utiliser

1. Créez une nouvelle issue ou commentez une issue existante
2. Incluez la commande `/mockup` suivie de l'URL de votre image
   
   Exemple :
   ```
   /mockup https://example.com/mon-image.png
   ```

3. L'action GitHub va automatiquement :
   - Télécharger l'image
   - Créer le mockup
   - Poster le résultat en commentaire

## Configuration requise

- Python 3.x
- Pillow (PIL)
- Requests

## Structure du projet

```
.
├── .github/
│   ├── workflows/
│   │   └── mockup_workflow.yml
│   └── scripts/
│       └── process_image.py
├── phone_mockup.png
└── README.md
```

## Limitations

- Les images doivent être accessibles publiquement
- Formats supportés : PNG, JPEG, GIF
- Taille maximale : 10MB

## Développement local

Pour tester localement :

1. Installez les dépendances :
   ```bash
   pip install pillow requests
   ```

2. Exécutez le script :
   ```bash
   python .github/scripts/process_image.py
   ```
