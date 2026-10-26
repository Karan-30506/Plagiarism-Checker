from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Stop:
    code: str
    name: str
    zone: int


STOPS = {
    "LIB": Stop("LIB", "Central Library", 1),
    "SCI": Stop("SCI", "Science Hall", 1),
    "ART": Stop("ART", "Arts Quad", 1),
    "GYM": Stop("GYM", "Sports Centre", 2),
    "RES": Stop("RES", "North Residence", 2),
    "MED": Stop("MED", "Medical Campus", 3),
}
ROUTES = {
    "LIB": ("SCI", "ART"),
    "SCI": ("LIB", "GYM"),
    "ART": ("LIB", "RES"),
    "GYM": ("SCI", "RES", "MED"),
    "RES": ("ART", "GYM", "MED"),
    "MED": ("GYM", "RES"),
}


def find_route(origin: str, destination: str) -> list[str]:
    if origin not in STOPS or destination not in STOPS:
        return []
    pending = deque([origin])
    parent = {origin: ""}
    while pending:
        stop = pending.popleft()
        if stop == destination:
            break
        for next_stop in ROUTES[stop]:
            if next_stop not in parent:
                parent[next_stop] = stop
                pending.append(next_stop)
    if destination not in parent:
        return []
    path = []
    while parent[destination]:
        path.append(destination)
        destination = parent[destination]
    return [origin, *reversed(path)]


def estimate_minutes(path: list[str], minutes_per_leg: int = 7) -> int:
    return max(0, len(path) - 1) * minutes_per_leg


def calculate_fare(path: list[str]) -> int:
    if len(path) < 2:
        return 0
    zones = {STOPS[stop].zone for stop in path}
    return 150 + 50 * (len(zones) - 1)


def format_itinerary(path: list[str]) -> str:
    if not path:
        return "No shuttle route is available."
    names = " -> ".join(STOPS[stop].name for stop in path)
    return (
        f"{names}\n"
        f"Travel time: {estimate_minutes(path)} minutes\n"
        f"Fare: {calculate_fare(path)} cents"
    )


def arrival_time(path: list[str], start: datetime) -> datetime:
    trip = estimate_minutes(path) + 4 * max(0, len(path) - 2)
    return start + timedelta(minutes=trip)


def passenger_message(path: list[str], start: datetime) -> str:
    if not path:
        return "No service found."
    arrival = arrival_time(path, start)
    return f"Estimated arrival: {arrival:%H:%M}; keep your pass ready."


def stops_nearby(stop_code: str, maximum_legs: int = 2) -> dict[str, int]:
    if stop_code not in STOPS:
        return {}
    leg_count = {stop_code: 0}
    pending = deque([stop_code])
    while pending:
        current = pending.popleft()
        if leg_count[current] >= maximum_legs:
            continue
        for neighbour in ROUTES[current]:
            if neighbour not in leg_count:
                leg_count[neighbour] = leg_count[current] + 1
                pending.append(neighbour)
    return {code: count for code, count in leg_count.items() if code != stop_code}


if __name__ == "__main__":
    stops = find_route("LIB", "MED")
    print(format_itinerary(stops))
    print(passenger_message(stops, datetime.now()))
