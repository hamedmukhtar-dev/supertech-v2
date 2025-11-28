# core/travel_ndc/offer_builder.py
import random

def generate_flight_offers(query):
    return [
        {
            "from": query.get("from", "KRT"),
            "to": query.get("to", "DXB"),
            "price": random.randint(200, 800),
            "fare": random.choice(["Basic", "Flex", "Premium"]),
            "airline": random.choice(["HN", "SA", "GL", "NX"]),
        }
        for _ in range(5)
    ]