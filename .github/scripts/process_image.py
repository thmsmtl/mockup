import os
import re
import json
import requests
from PIL import Image
from io import BytesIO

def get_image_url_from_comment(body):
    """Extraire l'URL de l'image du commentaire"""
    pattern = r'/mockup\s+(https?://[^\s]+)'
    match = re.search(pattern, body)
    return match.group(1) if match else None

def download_image(url):
    """Télécharger l'image depuis l'URL"""
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

def create_mockup(input_image):
    """Créer le mockup à partir de l'image d'entrée"""
    # Dimensions du mockup iPhone
    PHONE_WIDTH = 1242
    PHONE_HEIGHT = 2688
    SCREEN_WIDTH = 1080
    SCREEN_HEIGHT = 2340
    
    # Charger le template du mockup avec le chemin absolu
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    mockup_path = os.path.join(repo_root, 'phone_mockup.png')
    
    print(f"Recherche du template mockup à : {mockup_path}")
    mockup_template = Image.open(mockup_path).convert('RGBA')
    
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
    
    # Centrer l'image
    temp_image = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 0))
    paste_x = (SCREEN_WIDTH - new_width) // 2
    paste_y = (SCREEN_HEIGHT - new_height) // 2
    temp_image.paste(input_image, (paste_x, paste_y))
    
    # Créer l'image finale
    final_image = Image.new('RGBA', (PHONE_WIDTH, PHONE_HEIGHT), (0, 0, 0, 0))
    x_offset = (PHONE_WIDTH - SCREEN_WIDTH) // 2
    y_offset = (PHONE_HEIGHT - SCREEN_HEIGHT) // 2
    final_image.paste(temp_image, (x_offset, y_offset))
    
    # Ajouter le template
    final_image = Image.alpha_composite(final_image, mockup_template)
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
        # Lire l'événement GitHub
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if not event_path:
            raise ValueError("GITHUB_EVENT_PATH non défini")
            
        with open(event_path) as f:
            event = json.load(f)
        
        # Extraire l'URL de l'image
        body = event.get('comment', {}).get('body') or event['issue']['body']
        image_url = get_image_url_from_comment(body)
        
        if not image_url:
            raise ValueError("Aucune URL d'image trouvée dans le commentaire")
        
        print(f"Téléchargement de l'image depuis : {image_url}")
        input_image = download_image(image_url)
        
        print("Génération du mockup...")
        mockup = create_mockup(input_image)
        
        # Sauvegarder le résultat
        output_path = 'mockup_result.png'
        mockup.save(output_path)
        print(f"Mockup sauvegardé dans : {output_path}")
        
        # Poster le résultat
        issue_number = event['issue']['number']
        success = post_comment(issue_number, output_path)
        
        if success:
            print("Mockup généré et posté avec succès!")
        else:
            print("Erreur lors du post du commentaire")
        
    except Exception as e:
        print(f"Erreur : {str(e)}")
        raise e

if __name__ == "__main__":
    main()
