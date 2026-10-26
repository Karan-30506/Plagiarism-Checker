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
        raise ValueError("Both stops must be in the campus directory.")
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


def main() -> None:
    path = find_route("LIB", "MED")
    print(format_itinerary(path))


if __name__ == "__main__":
    main()
