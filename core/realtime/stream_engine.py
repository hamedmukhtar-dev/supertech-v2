# core/realtime/stream_engine.py
import time
import random

def generate_realtime_events():
    while True:
        yield {
            "timestamp": time.time(),
            "users_online": random.randint(10, 120),
            "ai_events": random.randint(1, 10),
            "fraud_alerts": random.randint(0, 2),
            "bookings_simulated": random.randint(0, 5),
        }
        time.sleep(1)