import os
import re
import json
import requests
from PIL import Image
from io import BytesIO

def debug_print_event(event):
    """Afficher les détails de l'événement GitHub pour le debug"""
    print("\n=== Détails de l'événement GitHub ===")
    print(f"Type d'événement : {event.get('action', 'inconnu')}")
    print(f"Issue number : {event.get('issue', {}).get('number', 'inconnu')}")
    if 'comment' in event:
        print("Source : Commentaire")
        print(f"Contenu : {event['comment'].get('body', 'vide')}")
    else:
        print("Source : Corps de l'issue")
        print(f"Contenu : {event.get('issue', {}).get('body', 'vide')}")
    print("=====================================\n")

def get_image_url_from_comment(body):
    """Extraire l'URL de l'image du commentaire"""
    if not body:
        raise ValueError("Le contenu du message est vide")
    
    print(f"\nRecherche de l'URL dans : {body}")
    pattern = r'/mockup\s+(https?://[^\s]+)'
    match = re.search(pattern, body)
    if not match:
        raise ValueError("Aucune URL d'image trouvée dans le commentaire")
    
    url = match.group(1)
    print(f"URL extraite : {url}")
    return url

def download_image(url):
    """Télécharger l'image depuis l'URL"""
    print(f"\nTéléchargement de l'image...")
    print(f"URL : {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        print(f"Content-Type reçu : {content_type}")
        
        if not content_type.startswith('image/'):
            raise ValueError(f"Le contenu n'est pas une image (Content-Type: {content_type})")
        
        content_length = len(response.content)
        print(f"Taille du contenu : {content_length} bytes")
        
        if content_length == 0:
            raise ValueError("Le contenu téléchargé est vide")
        
        image_data = BytesIO(response.content)
        image = Image.open(image_data)
        print(f"Image chargée avec succès : {image.format} {image.size}")
        return image
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erreur lors du téléchargement : {str(e)}")
    except Image.UnidentifiedImageError:
        raise ValueError("Le fichier téléchargé n'est pas une image valide")

def create_mockup(input_image):
    """Créer le mockup à partir de l'image d'entrée"""
    print("\nCréation du mockup...")
    
    # Dimensions du mockup iPhone
    PHONE_WIDTH = 1242
    PHONE_HEIGHT = 2688
    SCREEN_WIDTH = 1080
    SCREEN_HEIGHT = 2340
    
    # Charger le template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    mockup_path = os.path.join(repo_root, 'phone_mockup.png')
    
    print(f"Chemin du template : {mockup_path}")
    if not os.path.exists(mockup_path):
        print("\nRecherche du template dans le répertoire courant...")
        mockup_path = 'phone_mockup.png'
        if not os.path.exists(mockup_path):
            raise FileNotFoundError(f"Template introuvable. Chemins essayés : {repo_root}/phone_mockup.png, ./phone_mockup.png")
    
    print(f"Chargement du template depuis : {mockup_path}")
    mockup_template = Image.open(mockup_path).convert('RGBA')
    print(f"Template chargé : {mockup_template.format} {mockup_template.size}")
    
    # Redimensionner l'image source
    input_image = input_image.convert('RGBA')
    img_ratio = input_image.width / input_image.height
    screen_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
    
    if img_ratio > screen_ratio:
        new_width = SCREEN_WIDTH
        new_height = int(SCREEN_WIDTH / img_ratio)
    else:
        new_height = SCREEN_HEIGHT
        new_width = int(SCREEN_HEIGHT * img_ratio)
    
    input_image = input_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"Image redimensionnée : {new_width}x{new_height}")
    
    # Créer l'image finale
    final_image = Image.new('RGBA', (PHONE_WIDTH, PHONE_HEIGHT), (0, 0, 0, 0))
    x_offset = (PHONE_WIDTH - new_width) // 2
    y_offset = (PHONE_HEIGHT - new_height) // 2
    final_image.paste(input_image, (x_offset, y_offset))
    final_image = Image.alpha_composite(final_image, mockup_template)
    
    print("Mockup généré avec succès")
    return final_image

def post_comment(issue_number, image_path):
    """Poster un commentaire avec l'image générée"""
    headers = {
        'Authorization': f"token {os.environ['GITHUB_TOKEN']}",
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Upload l'image
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/issues/{issue_number}/comments",
            headers=headers,
            json={'body': '🎨 Voici votre mockup généré !\n\n![Mockup]({image_url})'}
        )
    
    return response.status_code == 201

def main():
    try:
        print("\n=== Démarrage du générateur de mockup ===")
        
        # Lire l'événement GitHub
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if not event_path:
            raise ValueError("Variable GITHUB_EVENT_PATH non définie")
        
        print(f"Lecture de l'événement : {event_path}")
        with open(event_path) as f:
            event = json.load(f)
        
        debug_print_event(event)
        
        # Extraire l'URL
        body = event.get('comment', {}).get('body') or event.get('issue', {}).get('body')
        image_url = get_image_url_from_comment(body)
        
        # Télécharger et traiter l'image
        input_image = download_image(image_url)
        mockup = create_mockup(input_image)
        
        # Sauvegarder le résultat
        output_path = 'mockup_result.png'
        mockup.save(output_path, 'PNG')
        print(f"\nMockup sauvegardé : {output_path}")
        
        # Poster le résultat
        issue_number = event['issue']['number']
        success = post_comment(issue_number, output_path)
        
        if success:
            print("Mockup généré et posté avec succès!")
        else:
            print("Erreur lors du post du commentaire")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        raise e

if __name__ == "__main__":
    main()
