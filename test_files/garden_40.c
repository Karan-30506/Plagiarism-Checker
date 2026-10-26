#include <stdbool.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    const char *name;
    int moisture;
    int rain_chance;
    bool enabled;
} GardenBed;

static GardenBed beds[] = {
    {"herbs", 31, 10, true},
    {"tomatoes", 24, 5, true},
    {"fern-house", 68, 0, true},
    {"seedlings", 19, 35, true},
};

static int watering_minutes(const GardenBed *bed) {
    if (!bed->enabled || bed->rain_chance >= 60 || bed->moisture >= 65) {
        return 0;
    }
    if (bed->moisture < 25) {
        return 18;
    }
    if (bed->moisture < 40) {
        return 11;
    }
    return 5;
}

static const char *watering_reason(const GardenBed *bed, int minutes) {
    if (!bed->enabled) {
        return "bed is disabled";
    }
    if (bed->rain_chance >= 60) {
        return "rain is expected";
    }
    if (minutes == 0) {
        return "soil is damp enough";
    }
    return "soil needs moisture";
}

static int total_water_minutes(void) {
    int total = 0;
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        total += watering_minutes(&beds[i]);
    }
    return total;
}

static const GardenBed *find_bed(const char *name) {
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        if (strcmp(beds[i].name, name) == 0) {
            return &beds[i];
        }
    }
    return NULL;
}

static void print_sensor_card(const GardenBed *bed, int hour) {
    if (!bed) {
        puts("No sensor found for that bed.");
        return;
    }
    int minutes = watering_minutes(bed);
    const char *window = (hour < 6 || hour >= 20) ? "overnight window" : "daytime window";
    printf("Bed: %s\nMoisture: %d%%\nRain chance: %d%%\n",
           bed->name, bed->moisture, bed->rain_chance);
    printf("Decision: %s; runtime %d min (%s)\n",
           watering_reason(bed, minutes), minutes, window);
}

static int pump_start_hour(int hour, int minutes_needed) {
    if (minutes_needed == 0) {
        return -1;
    }
    return (hour < 5 || hour >= 21) ? 5 : hour;
}

static void print_zone_report(int zone) {
    int beds_in_zone = 0;
    int total_runtime = 0;
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        if ((int)(i % 2) + 1 != zone) {
            continue;
        }
        ++beds_in_zone;
        total_runtime += watering_minutes(&beds[i]);
    }
    printf("Zone %d: %d beds, %d minutes scheduled\n",
           zone, beds_in_zone, total_runtime);
}

static void print_plan(void) {
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        int minutes = watering_minutes(&beds[i]);
        int start_hour = pump_start_hour(22, minutes);
        printf("%-12s %2d min - %s", beds[i].name, minutes,
               watering_reason(&beds[i], minutes));
        if (start_hour >= 0) {
            printf(" at %02d:00", start_hour);
        }
        putchar('\n');
    }
    printf("Total valve time: %d minutes\n", total_water_minutes());
}

int main(void) {
    print_plan();
    print_sensor_card(find_bed("tomatoes"), 22);
    print_zone_report(1);
    print_zone_report(2);
    return 0;
}
