import torch
from PIL import Image
from torchvision import transforms
import pinecone
from config import Config
import unicodedata
import re
import time
import urllib.parse

def to_ascii_id(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-zA-Z0-9_.-]', '_', s)
    return s

def create_google_maps_url(address):
    """
    Create a Google Maps URL for the given address.
    
    Args:
        address: The address string (e.g., "26 rue etex, 75018 Paris, France")
    
    Returns:
        Google Maps URL
    """
    # Encode the address for URL
    encoded_address = urllib.parse.quote(address)
    return f"https://www.google.com/maps/place/{encoded_address}"

# --- Load DINOv2 Model ---
device = 'cuda' if torch.cuda.is_available() else 'cpu'

def load_dinov2_model():
    """Load DINOv2 model with retry logic for rate limiting"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Loading DINOv2 model (attempt {attempt + 1}/{max_retries})...")
            # Using dinov2_vitb14 which produces 768-dimensional vectors
            model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14', trust_repo=True)
            model = model.to(device)
            model.eval()
            print("DINOv2 model loaded successfully!")
            return model
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("Failed to load DINOv2 model after all retries")
                raise e

# Global variable for the model (will be loaded lazily)
dinov2 = None

# --- Preprocessing for DINOv2 ---
preprocess = transforms.Compose([
    transforms.Resize(224, interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def query_image_unique_addresses(image_path, top_k=5, max_results=50):
    """
    Query image and return top_k unique addresses.
    
    Args:
        image_path: Path to the image file
        top_k: Number of unique addresses to return (default: 5)
        max_results: Maximum results to fetch from Pinecone to find unique addresses (default: 50)
    
    Returns:
        List of dictionaries with unique addresses and their scores
    """
    global dinov2
    
    # Load model lazily if not already loaded
    if dinov2 is None:
        dinov2 = load_dinov2_model()
    
    # Load and preprocess image
    img = Image.open(image_path).convert('RGB')
    img_tensor = preprocess(img).unsqueeze(0).to(device)
    
    # Generate vector embedding
    with torch.no_grad():
        features = dinov2(img_tensor)
        vector = features.squeeze().cpu().numpy().tolist()
    
    # Initialize Pinecone
    pc = pinecone.Pinecone(api_key=Config.PINECONE_API_KEY)
    index = pc.Index(Config.PINECONE_INDEX_NAME)
    
    # Query Pinecone with more results to ensure we get enough unique addresses
    query_results = index.query(
        vector=vector, 
        top_k=max_results, 
        include_metadata=True
    )
    
    # Extract unique addresses
    unique_addresses = {}
    results = []
    
    for match in query_results['matches']:
        meta = match.get('metadata', {})
        address = meta.get('address')
        score = match.get('score', 0)
        
        # Skip if no address or already found this address
        if not address or address in unique_addresses:
            continue
            
        # Store the best score for this address
        if address not in unique_addresses or score > unique_addresses[address]['score']:
            unique_addresses[address] = {
                'score': score,
                'id': match.get('id'),
                'address': address,
                'google_maps_url': create_google_maps_url(address)
            }
        
        # Stop when we have enough unique addresses
        if len(unique_addresses) >= top_k:
            break
    
    # Convert to list and sort by score
    results = list(unique_addresses.values())
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return only the requested number of results
    return results[:top_k]

def query_image(image_path, top_k=5):
    """
    Legacy function for backward compatibility.
    Now returns unique addresses by default.
    """
    return query_image_unique_addresses(image_path, top_k=top_k)

if __name__ == "__main__":
    # Example usage
    test_image = input("Enter path to image to query: ")
    results = query_image_unique_addresses(test_image, top_k=5)
    print(f"\nFound {len(results)} unique addresses:")
    for i, res in enumerate(results, 1):
        print(f"{i}. Address: {res['address']}")
        print(f"   Score: {res['score']:.4f}")
        print(f"   Google Maps: {res['google_maps_url']}")
        print() 