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

function createCheckInList(eventId) {
  const event = findEvent(eventId);
  if (!event) {
    throw new Error("Cannot check in attendees for an unknown event.");
  }
  return event.attendees
    .map((person) => ({ ...person, checkedIn: false }))
    .sort((left, right) => left.name.localeCompare(right.name));
}

function attendanceRate(event) {
  if (event.attendees.length === 0) {
    return 0;
  }
  const checkedIn = event.attendees.filter((person) => person.checkedIn).length;
  return Math.round((checkedIn / event.attendees.length) * 100);
}

function checkInAttendee(eventId, email) {
  const event = findEvent(eventId);
  if (!event) {
    return { ok: false, message: "Unknown event." };
  }
  const attendee = event.attendees.find(
    (person) => person.email === normalizeEmail(email)
  );
  if (!attendee) {
    return { ok: false, message: "No registration found for that address." };
  }
  if (attendee.checkedIn) {
    return { ok: false, message: "Attendee was already checked in." };
  }
  attendee.checkedIn = true;
  return { ok: true, message: `Welcome, ${attendee.name}.` };
}

function attendanceReport() {
  return events.map((event) => ({
    event: event.title,
    total: event.attendees.length,
    checkedIn: event.attendees.filter((person) => person.checkedIn).length,
    percentage: attendanceRate(event),
  }));
}

function findUnclaimedSeats(eventId) {
  const event = findEvent(eventId);
  if (!event) {
    return 0;
  }
  return Math.max(event.capacity - event.attendees.length, 0);
}

function reminderList(eventId) {
  const event = findEvent(eventId);
  if (!event) {
    return [];
  }
  return event.attendees
    .filter((person) => !person.checkedIn)
    .map((person) => ({
      name: person.name,
      address: person.email,
      subject: `Reminder: ${event.title} is coming up`,
    }));
}

registerAttendee("EV-14", "Mira Patel", "MIRA@example.org");
checkInAttendee("EV-14", "mira@example.org");
console.table(events.map(eventCard));
console.log(createCheckInList("EV-14"));
console.table(attendanceReport());
console.log(reminderList("EV-14"));
