CREATE TABLE glacier_observation (
    station_code VARCHAR(24),
    altitude_m INTEGER,
    salinity_ppm DECIMAL(8, 3),
    recorded_at TIMESTAMP
);

INSERT INTO glacier_observation
    (station_code, altitude_m, salinity_ppm, recorded_at)
VALUES
    ('K-441', 2860, 3.125, CURRENT_TIMESTAMP);

SELECT
    station_code,
    AVG(salinity_ppm) AS mean_salt
FROM glacier_observation
GROUP BY station_code
HAVING COUNT(*) > 4
ORDER BY mean_salt DESC;
