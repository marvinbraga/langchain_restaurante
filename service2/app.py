import json
import logging
from typing import List, Optional

import redis
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ConversationModel(BaseModel):
    conversation: List[Message]


class RedisStore:
    def __init__(self, host: str, port: int, db: int):
        self.client = redis.Redis(host=host, port=port, db=db)

    def get(self, key: str) -> Optional[dict]:
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: dict):
        self.client.set(key, json.dumps(value))


class Assistant:
    def __init__(self, service_url: str):
        self.service_url = service_url

    def get_reply(self, conversation_id: str, conversation: dict) -> str:
        response = requests.post(f"{self.service_url}/{conversation_id}", json=conversation)
        response.raise_for_status()
        return response.json()["reply"]


class Conversation:
    def __init__(self, initial_message: Optional[str] = None):
        if initial_message:
            self.conversation = [{"role": "system", "content": initial_message}]
        else:
            self.conversation = []

    def add_message(self, message: dict):
        self.conversation.append(message)

    def get_messages(self) -> List[dict]:
        return self.conversation


class ConversationService:

    def __init__(self, store, assistant):
        self.store = store
        self.assistant = assistant

    def get_conversation(self, conversation_id: str):
        conversation_data = self.store.get(conversation_id)
        if not conversation_data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation_data

    def post_conversation(self, conversation_id: str, conversation_data: ConversationModel):
        existing_data = self.store.get(conversation_id)
        conversation = Conversation()
        if existing_data:
            conversation.conversation = existing_data["conversation"]
        else:
            conversation.add_message({"role": "system", "content": "You are a helpful assistant."})

        user_message = conversation_data.conversation[-1]
        conversation.add_message(user_message.model_dump())

        assistant_message_content = self.assistant.get_reply(
            conversation_id,
            {"conversation": conversation.get_messages()}
        )
        conversation.add_message({"role": "assistant", "content": assistant_message_content})

        self.store.set(conversation_id, {"conversation": conversation.get_messages()})

        return {"conversation": conversation.get_messages()}


service = ConversationService(
    RedisStore(host='redis', port=6379, db=0),
    Assistant(service_url='http://service3:80/service3')
)


@app.get("/service2/{conversation_id}")
async def get_conversation_endpoint(conversation_id: str):
    return service.get_conversation(conversation_id)


@app.post("/service2/{conversation_id}")
async def post_conversation_endpoint(conversation_id: str, conversation_data: ConversationModel):
    return service.post_conversation(conversation_id, conversation_data)
