from datetime import datetime

class ChatMessage:
    def __init__(self, username: str, timestamp: datetime, content: str, role: str, category_id: int):
        self.username = username
        self.timestamp = timestamp
        self.content = content
        self.role = role
        self.category_id = category_id

    def __repr__(self):
        return (f"ChatMessage(username='{self.username}', timestamp={self.timestamp}, "
                f"content='{self.content}', role='{self.role}', category_id={self.category_id})")