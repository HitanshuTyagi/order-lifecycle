from enum import Enum


class UserRole(str, Enum):
    PICKER = "picker"
    DELIVERY_BOY = "delivery_boy"


class OrderStatus(str, Enum):
    CREATED = "created"
    ASSIGNED_TO_PACKER = "assigned_to_packer"
    PACKED = "packed"
    ASSIGNED_TO_RIDER = "assigned_to_rider"
    DELIVERED = "delivered"