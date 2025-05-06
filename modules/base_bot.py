# base_bot.py
from abc import ABC, abstractmethod

# Abstract base class for a bot (to demonstrate abstraction)
class BaseBot(ABC):

    # Abstract method for sending a message
    @abstractmethod
    def send_message(self, text):
        pass

    # Abstract method for sending a photo (from file or bytes)
    @abstractmethod
    def send_photo(self, data):
        pass
