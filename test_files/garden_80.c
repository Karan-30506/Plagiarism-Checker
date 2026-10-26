#include <stdbool.h>
#include <stdio.h>

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
    if (!bed->enabled || bed->rain_chance >= 60 || bed->moisture >= 70) {
        return 0;
    }
    if (bed->moisture < 28) {
        return 16;
    }
    if (bed->moisture < 42) {
        return 10;
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
    return "soil is dry";
}

static int total_water_minutes(void) {
    int total = 0;
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        total += watering_minutes(&beds[i]);
    }
    return total;
}

static void print_plan(void) {
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        int minutes = watering_minutes(&beds[i]);
        printf("%-12s %2d min - %s\n", beds[i].name, minutes,
               watering_reason(&beds[i], minutes));
    }
    printf("Total valve time: %d minutes\n", total_water_minutes());
}

int main(void) {
    print_plan();
    return 0;
}
