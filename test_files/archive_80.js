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

function searchEvents(query) {
  const searchTerm = query.trim().toLowerCase();
  return events.filter((event) => event.title.toLowerCase().includes(searchTerm));
}

function waitlistFor(eventId) {
  const event = findEvent(eventId);
  if (!event || remainingSeats(event) > 0) {
    return [];
  }
  return event.waitlist || [];
}

registerAttendee("EV-14", "Mira Patel", "MIRA@example.org");
console.table(events.map(eventCard));
console.log(searchEvents("bird"));
