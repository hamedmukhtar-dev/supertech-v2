from core.config import settings

def publish(event: dict):
    # Placeholder: route to Redis/Kafka adapter
    # For now, just print; adapters will be implemented later
    print("Realtime publish:", event)
