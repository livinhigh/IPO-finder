from __future__ import annotations

from threading import Lock
from typing import List


class SubscriberStore:
    _instance: "SubscriberStore | None" = None
    _lock = Lock()

    def __new__(cls) -> "SubscriberStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = []
        return cls._instance

    def add(self, email: str) -> bool:
        if email in self._subscribers:
            return False
        self._subscribers.append(email)
        return True

    def list_all(self) -> List[str]:
        return list(self._subscribers)
