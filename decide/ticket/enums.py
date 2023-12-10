from enum import Enum


class TicketStatus(Enum):
    PENDING = "Pending"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"

    def __str__(self):
        return self.value
    
    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)