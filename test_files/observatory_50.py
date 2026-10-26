from dataclasses import dataclass
from collections import deque


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
        raise KeyError("Stop code is not listed.")
    queue = deque([(origin, [origin])])
    visited = {origin}
    while queue:
        current, path = queue.popleft()
        if current == destination:
            return path
        for neighbour in ROUTES[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append((neighbour, path + [neighbour]))
    return []


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


def list_accessible_stops(origin: str) -> list[str]:
    remaining = set(STOPS) - {origin}
    return sorted(remaining, key=lambda code: STOPS[code].name)


def campus_notice(path: list[str]) -> str:
    if len(path) >= 4:
        return "This journey crosses the campus; allow extra time."
    return "This is a short campus trip."


def stops_in_zone(zone: int) -> list[Stop]:
    return sorted(
        (stop for stop in STOPS.values() if stop.zone == zone),
        key=lambda stop: stop.name,
    )


def accessible_destinations(origin: str) -> list[tuple[str, int]]:
    if origin not in STOPS:
        return []
    distances = {origin: 0}
    frontier = deque([origin])
    while frontier:
        current = frontier.popleft()
        for neighbour in ROUTES[current]:
            if neighbour not in distances:
                distances[neighbour] = distances[current] + 1
                frontier.append(neighbour)
    return sorted(
        ((code, distance) for code, distance in distances.items() if code != origin),
        key=lambda item: (item[1], STOPS[item[0]].name),
    )


def transfer_count(path: list[str]) -> int:
    if len(path) < 3:
        return 0
    changes = 0
    previous_zone = STOPS[path[0]].zone
    for stop_code in path[1:]:
        current_zone = STOPS[stop_code].zone
        if current_zone != previous_zone:
            changes += 1
            previous_zone = current_zone
    return changes


def journey_card(path: list[str]) -> dict[str, object]:
    return {
        "stops": [STOPS[code].name for code in path],
        "distance_in_legs": max(0, len(path) - 1),
        "zone_changes": transfer_count(path),
        "advice": campus_notice(path),
    }


def main() -> None:
    path = find_route("LIB", "MED")
    print(format_itinerary(path))
    print(campus_notice(path))
    print("Nearby stops:", accessible_destinations("LIB"))
    print("Zone 2:", [stop.name for stop in stops_in_zone(2)])
    print("Journey card:", journey_card(path))


if __name__ == "__main__":
    main()
