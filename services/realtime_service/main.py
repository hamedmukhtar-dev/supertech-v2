from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from services.realtime_service.producers import producer

app = FastAPI(title="HUMAIN — Realtime Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # echo back for now
            await websocket.send_text(f"echo: {data}")
    except Exception:
        await websocket.close()

@app.post("/produce")
def produce_event(payload: dict):
    producer.publish(payload)
    return {"status": "published"}
