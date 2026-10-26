const events = [
  { id: "EV-14", title: "Night Sky Walk", capacity: 18, attendees: [] },
  { id: "EV-22", title: "Printmaking Workshop", capacity: 12, attendees: [] },
  { id: "EV-37", title: "Coastal Bird Count", capacity: 24, attendees: [] },
];

function normalizeEmail(email) {
  return email.trim().toLowerCase();
}

function findEvent(eventId) {
  return events.find((event) => event.id === eventId);
}

function registerAttendee(eventId, displayName, email) {
  const event = findEvent(eventId);
  if (!event) {
    return { ok: false, message: "Event was not found." };
  }
  const address = normalizeEmail(email);
  if (!displayName.trim() || !address.includes("@")) {
    return { ok: false, message: "Enter a name and valid email address." };
  }
  if (event.attendees.some((person) => person.email === address)) {
    return { ok: false, message: "This address is already registered." };
  }
  if (event.attendees.length >= event.capacity) {
    return { ok: false, message: "The event is full." };
  }
  event.attendees.push({ name: displayName.trim(), email: address });
  return { ok: true, message: `Registered for ${event.title}.` };
}

function cancelRegistration(eventId, email) {
  const event = findEvent(eventId);
  if (!event) {
    return false;
  }
  const address = normalizeEmail(email);
  const before = event.attendees.length;
  event.attendees = event.attendees.filter((person) => person.email !== address);
  return before !== event.attendees.length;
}

function remainingSeats(event) {
  return Math.max(0, event.capacity - event.attendees.length);
}

function eventCard(event) {
  return {
    title: event.title,
    registered: event.attendees.length,
    seatsLeft: remainingSeats(event),
    status: remainingSeats(event) === 0 ? "full" : "open",
  };
}

function buildSchedule(dayEvents, roomAvailability) {
  const assignments = [];
  for (const event of dayEvents) {
    const room = roomAvailability.find(
      (candidate) => candidate.seats >= event.capacity && !candidate.booked
    );
    if (room) {
      room.booked = true;
      assignments.push({ eventId: event.id, room: room.name });
    } else {
      assignments.push({ eventId: event.id, room: null });
    }
  }
  return assignments;
}

function registrationSummary() {
  return events.map((event) => ({
    ...eventCard(event),
    fillPercent: Math.round((event.attendees.length / event.capacity) * 100),
  }));
}

function allocateRooms(dayEvents, rooms) {
  const schedule = new Map();
  const orderedEvents = [...dayEvents].sort(
    (first, second) => second.capacity - first.capacity
  );
  for (const event of orderedEvents) {
    const room = rooms
      .filter((candidate) => candidate.seats >= event.capacity)
      .sort((first, second) => first.seats - second.seats)[0];
    if (!room) {
      schedule.set(event.id, { room: null, note: "No room has enough seats." });
      continue;
    }
    rooms = rooms.filter((candidate) => candidate.name !== room.name);
    schedule.set(event.id, { room: room.name, note: "Room reserved." });
  }
  return schedule;
}

function attendeeSearch(phrase) {
  const needle = phrase.trim().toLowerCase();
  const matches = [];
  for (const event of events) {
    for (const person of event.attendees) {
      if (
        person.name.toLowerCase().includes(needle) ||
        person.email.includes(needle)
      ) {
        matches.push({ eventId: event.id, eventTitle: event.title, ...person });
      }
    }
  }
  return matches;
}

function exportRoster(eventId) {
  const event = findEvent(eventId);
  if (!event) {
    return "";
  }
  const header = "name,email";
  const rows = event.attendees.map(
    (person) => `"${person.name.replaceAll('"', '""')}",${person.email}`
  );
  return [header, ...rows].join("\n");
}

registerAttendee("EV-14", "Mira Patel", "MIRA@example.org");
console.table(registrationSummary());
console.log(allocateRooms(events, [
  { name: "Gallery A", seats: 20 },
  { name: "Studio C", seats: 14 },
]));
console.log(exportRoster("EV-14"));
