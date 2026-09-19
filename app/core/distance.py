"""
Geographical distance utilities.

The calculation uses the Haversine formula to calculate the
great-circle distance between two latitude/longitude coordinates.
"""

from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0


def calculate_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate the great-circle distance between two coordinates.

    Latitude and longitude are supplied in degrees.
    The result is returned in kilometres.
    """

    # Convert degrees to radians because Python's trigonometric
    # functions operate on radians.
    lat1 = radians(latitude_1)
    lon1 = radians(longitude_1)

    lat2 = radians(latitude_2)
    lon2 = radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Haversine formula.
    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    # Protect against tiny floating-point errors.
    a = min(1.0, max(0.0, a))

    angular_distance = 2 * asin(sqrt(a))

    return EARTH_RADIUS_KM * angular_distance


def calculate_route_distance_km(
    warehouse: tuple[float, float],
    stops: list[tuple[float, float]],
) -> float:
    """
    Calculate the chained warehouse → A → B → C distance.

    We deliberately do NOT calculate:

        warehouse → A
        warehouse → B
        warehouse → C

    because the rider is not returning to the warehouse between stops.
    """

    if not stops:
        return 0.0

    total_distance = 0.0

    previous_stop = warehouse

    for current_stop in stops:
        total_distance += calculate_distance_km(
            previous_stop[0],
            previous_stop[1],
            current_stop[0],
            current_stop[1],
        )

        previous_stop = current_stop

    return total_distance