import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")    
import django
django.setup()

from alarm_app.models import RoomObjects

objects = [
    {"name": "Water Bottle", "category": "other", "emoji": "🫗", "hint": "Find the bottle you drink from — kitchen or desk"},
    {"name": "Lamp", "category": "furniture", "emoji": "💡", "hint": "Find any lamp in your room and click it on"},
    {"name": "Chair", "category": "furniture", "emoji": "🪑", "hint": "Take a photo of a chair — doesn't have to be yours!"},
    {"name": "Keyboard", "category": "electronics", "emoji": "⌨️", "hint": "Find your computer keyboard"},
    {"name": "Coffee Mug", "category": "kitchen", "emoji": "☕", "hint": "Your mug — even an empty one counts!"},
    {"name": "Mirror", "category": "decor", "emoji": "🪞", "hint": "Find any mirror in the house"},
    {"name": "Plant", "category": "decor", "emoji": "🪴", "hint": "Any plant — real or fake — works!"},
    {"name": "Book", "category": "decor", "emoji": "📖", "hint": "Grab any book from your shelf"},
    {"name": "Shoes", "category": "other", "emoji": "👟", "hint": "Pick up or photograph a pair of shoes"},
    {"name": "Pillow", "category": "furniture", "emoji": "🛏️", "hint": "Photograph the pillow you were sleeping on"},
]


for obj in objects:
    RoomObjects.objects.get_or_create(name=obj["name"], defaults=obj)
    print(f"  ✅ {obj['emoji']} {obj['name']}")

print(f"\nTotal active objects: {RoomObjects.objects.filter(is_active=True).count()}")