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

static int water_budget_remaining(int daily_budget, int used_today) {
    int available = daily_budget - used_today;
    return available > 0 ? available : 0;
}

static int dry_bed_count(void) {
    int count = 0;
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        if (beds[i].enabled && beds[i].moisture < 40) {
            ++count;
        }
    }
    return count;
}

static int moisture_average(void) {
    int sum = 0;
    size_t count = sizeof(beds) / sizeof(beds[0]);
    for (size_t i = 0; i < count; ++i) {
        sum += beds[i].moisture;
    }
    return count == 0 ? 0 : sum / (int)count;
}

static void print_plan(void) {
    int available_minutes = water_budget_remaining(50, 12);
    for (size_t i = 0; i < sizeof(beds) / sizeof(beds[0]); ++i) {
        int requested = watering_minutes(&beds[i]);
        int approved = requested < available_minutes ? requested : available_minutes;
        available_minutes -= approved;
        printf("%-12s requested %2d min, scheduled %2d min - %s\n",
               beds[i].name, requested, approved,
               watering_reason(&beds[i], approved));
    }
    printf("Remaining daily pump budget: %d minutes\n", available_minutes);
    printf("Uncapped valve time: %d minutes\n", total_water_minutes());
    printf("Dry beds: %d; average moisture: %d%%\n",
           dry_bed_count(), moisture_average());
}

int main(void) {
    print_plan();
    return 0;
}
