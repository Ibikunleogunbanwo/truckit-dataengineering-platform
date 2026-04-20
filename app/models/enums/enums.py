from enum import Enum


class TruckType(str, Enum):
    cargo_van       = "cargo_van"
    small_truck     = "small_truck"
    medium_truck    = "medium_truck"
    large_truck     = "large_truck"
    specialty_truck = "specialty_truck"

class ServiceType(str, Enum):
    packing   = "packing"
    loading   = "loading"
    full_move = "full_move"