import requests
import os
from urllib.parse import urlparse

def download_image(url, filename):
    """Download an image from URL and save to media directory"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join('media/bookclub_images', filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def create_placeholder_images():
    """Download placeholder images for book clubs"""
    
    # Book club themed placeholder images from Unsplash
    images = [
        {
            'url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
            'filename': 'mystery_club.jpg'  # Books on shelf
        },
        {
            'url': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop',
            'filename': 'romance_club.jpg'  # Cozy reading setup
        },
        {
            'url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=400&h=300&fit=crop',
            'filename': 'scifi_club.jpg'  # Modern library
        },
        {
            'url': 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&h=300&fit=crop',
            'filename': 'literary_club.jpg'  # Classic books
        },
        {
            'url': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop',
            'filename': 'fantasy_club.jpg'  # Magical books setup
        },
        {
            'url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&h=300&fit=crop',
            'filename': 'ya_club.jpg'  # Young books
        },
        {
            'url': 'https://images.unsplash.com/photo-1491841573337-20c23e43dadc?w=400&h=300&fit=crop',
            'filename': 'nonfiction_club.jpg'  # Study books
        },
        {
            'url': 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&h=300&fit=crop',
            'filename': 'classic_club.jpg'  # Classic literature
        }
    ]
    
    print("Downloading placeholder images for book clubs...")
    
    for image in images:
        download_image(image['url'], image['filename'])
    
    print("Placeholder image download complete!")

if __name__ == "__main__":
    create_placeholder_images()
