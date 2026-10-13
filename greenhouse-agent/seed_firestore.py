"""Seed Firestore with initial houseplant inventory for greenhouse-agent."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-92a7633d9ea5"

PLANTS = [
    {
        "id": "monstera-deliciosa",
        "name": "Monstera Deliciosa",
        "scientific_name": "Monstera deliciosa",
        "light_level": "medium-to-bright-indirect",
        "watering_frequency_days": 7,
        "care_difficulty": "easy",
        "pet_safe": False,
        "description": "Iconic split-leaf houseplant that thrives in warm, humid indoor spaces with bright indirect light.",
        "soil_type": "Chunky, well-draining aroid mix (coco coir, perlite, orchid bark)",
        "in_stock": True,
        "price_usd": 29.99
    },
    {
        "id": "snake-plant",
        "name": "Snake Plant (Sansevieria)",
        "scientific_name": "Dracaena trifasciata",
        "light_level": "low-to-bright",
        "watering_frequency_days": 18,
        "care_difficulty": "beginner",
        "pet_safe": False,
        "description": "Extremely forgiving upright plant capable of surviving low light and sparse watering.",
        "soil_type": "Cactus & succulent mix with coarse pumice or sand",
        "in_stock": True,
        "price_usd": 19.99
    },
    {
        "id": "boston-fern",
        "name": "Boston Fern",
        "scientific_name": "Nephrolepis exaltata",
        "light_level": "medium-indirect",
        "watering_frequency_days": 4,
        "care_difficulty": "moderate",
        "pet_safe": True,
        "description": "Lush, feathery green fronds. Loves high humidity and consistently moist soil. Non-toxic to cats and dogs.",
        "soil_type": "Rich peat/coco moss-based mix with perlite",
        "in_stock": True,
        "price_usd": 24.50
    },
    {
        "id": "spider-plant",
        "name": "Spider Plant",
        "scientific_name": "Chlorophytum comosum",
        "light_level": "medium-indirect",
        "watering_frequency_days": 7,
        "care_difficulty": "beginner",
        "pet_safe": True,
        "description": "Fast-growing pet-safe plant with ribbon-like leaves producing little plantlets ('spiderettes').",
        "soil_type": "Standard well-aerated potting mix",
        "in_stock": True,
        "price_usd": 14.99
    },
    {
        "id": "calathea-orbifolia",
        "name": "Calathea Orbifolia",
        "scientific_name": "Goeppertia orbifolia",
        "light_level": "low-to-medium-indirect",
        "watering_frequency_days": 5,
        "care_difficulty": "intermediate",
        "pet_safe": True,
        "description": "Stunning oversized striped round leaves that pray and move with the day. Completely pet-safe.",
        "soil_type": "Moisture-retentive, airy blend with perlite and worm castings",
        "in_stock": True,
        "price_usd": 34.00
    },
    {
        "id": "fiddle-leaf-fig",
        "name": "Fiddle Leaf Fig",
        "scientific_name": "Ficus lyrata",
        "light_level": "bright-indirect",
        "watering_frequency_days": 9,
        "care_difficulty": "intermediate",
        "pet_safe": False,
        "description": "Popular statement tree with violin-shaped leathery leaves that needs consistent light and watering.",
        "soil_type": "Well-draining potting soil with bark and pumice",
        "in_stock": True,
        "price_usd": 45.00
    }
]

def seed():
    print(f"Connecting to Firestore with project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("plants")
    
    for plant in PLANTS:
        doc_id = plant["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(plant)
        print(f"Seeded: {plant['name']} ({doc_id})")

    print(f"Successfully seeded {len(PLANTS)} plants into 'plants' collection in Firestore!")

if __name__ == "__main__":
    seed()
