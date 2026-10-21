
CREATE TABLE city_daily_temperature (
    observation_id INTEGER PRIMARY KEY,
    observation_date TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    average_temp_c REAL NOT NULL,
    min_temp_c REAL NOT NULL,
    max_temp_c REAL NOT NULL
);

CREATE TABLE city_weather_details (
    observation_id INTEGER PRIMARY KEY,
    rainfall_mm REAL NOT NULL,
    wind_speed_kmh REAL,
    pressure_hpa REAL NOT NULL,
    sunshine_seconds REAL,
    FOREIGN KEY (observation_id)
        REFERENCES city_daily_temperature (observation_id)
);

ALTER TABLE city_daily_temperature
ADD COLUMN observation_year INTEGER NOT NULL DEFAULT 2020;


ALTER TABLE city_weather_details
ADD COLUMN rainy_day INTEGER NOT NULL DEFAULT 0 CHECK (rainy_day IN (0, 1));

INSERT INTO city_daily_temperature
    (observation_id, observation_date, city, average_temp_c, min_temp_c, max_temp_c, observation_year)
VALUES
    (1,  '2020-01-01', 'Mumbai', 24.9, 19.2, 29.9, 2020),
    (2,  '2020-02-01', 'Mumbai', 27.3, 21.0, 32.6, 2020),
    (3,  '2020-03-01', 'Mumbai', 27.7, 22.6, 31.9, 2020),
    (4,  '2020-04-01', 'Mumbai', 30.2, 26.4, 33.9, 2020),
    (5,  '2020-05-01', 'Mumbai', 31.1, 28.6, 34.0, 2020),
    (6,  '2020-06-01', 'Mumbai', 29.2, 26.0, 32.3, 2020),
    (7,  '2020-07-01', 'Mumbai', 28.1, 25.4, 30.5, 2020),
    (8,  '2020-08-01', 'Mumbai', 27.6, 25.0, 29.6, 2020),
    (9,  '2020-09-01', 'Mumbai', 28.4, 25.3, 31.4, 2020),
    (10, '2020-10-01', 'Mumbai', 29.2, 25.6, 32.7, 2020),
    (11, '2020-11-01', 'Mumbai', 28.7, 23.1, 33.9, 2020),
    (12, '2020-12-01', 'Mumbai', 26.6, 20.8, 32.3, 2020),
    (13, '2021-01-01', 'Mumbai', 25.9, 20.5, 30.9, 2021),
    (14, '2021-02-01', 'Mumbai', 27.3, 21.4, 32.9, 2021),
    (15, '2021-03-01', 'Mumbai', 29.7, 23.9, 35.0, 2021),
    (16, '2021-04-01', 'Mumbai', 30.0, 26.2, 33.6, 2021),
    (17, '2021-05-01', 'Mumbai', 30.7, 27.8, 33.8, 2021),
    (18, '2021-06-01', 'Mumbai', 28.6, 25.5, 31.5, 2021),
    (19, '2021-07-01', 'Mumbai', 28.6, 25.7, 30.8, 2021),
    (20, '2021-08-01', 'Mumbai', 27.8, 25.1, 30.0, 2021),
    (21, '2021-09-01', 'Mumbai', 27.7, 24.8, 30.1, 2021),
    (22, '2021-10-01', 'Mumbai', 29.4, 25.2, 33.5, 2021),
    (23, '2021-11-01', 'Mumbai', 29.5, 25.0, 34.1, 2021),
    (24, '2021-12-01', 'Mumbai', 25.8, 21.0, 30.6, 2021),
    (25, '2022-01-01', 'Mumbai', 24.5, 19.3, 29.3, 2022),
    (26, '2022-02-01', 'Mumbai', 25.3, 19.3, 30.5, 2022),
    (27, '2022-03-01', 'Mumbai', 30.0, 24.7, 34.9, 2022),
    (28, '2022-04-01', 'Mumbai', 30.6, 26.8, 34.5, 2022),
    (29, '2022-05-01', 'Mumbai', 30.9, 28.8, 34.0, 2022),
    (30, '2022-06-01', 'Mumbai', 29.3, 26.6, 32.9, 2022),
    (31, '2022-07-01', 'Mumbai', 27.8, 25.3, 29.8, 2022),
    (32, '2022-08-01', 'Mumbai', 27.7, 25.1, 30.3, 2022),
    (33, '2022-09-01', 'Mumbai', 27.5, 24.7, 30.2, 2022),
    (34, '2022-10-01', 'Mumbai', 28.4, 24.5, 32.4, 2022),
    (35, '2022-11-01', 'Mumbai', 27.9, 21.9, 33.6, 2022),
    (36, '2022-12-01', 'Mumbai', 27.3, 21.8, 32.5, 2022),
    (37, '2023-01-01', 'Mumbai', 24.4, 18.7, 29.5, 2023),
    (38, '2023-02-01', 'Mumbai', 28.1, 20.6, 34.2, 2023),
    (39, '2023-03-01', 'Mumbai', 28.9, 23.6, 33.5, 2023),
    (40, '2023-04-01', 'Mumbai', 30.0, 25.8, 33.8, 2023),
    (41, '2023-05-01', 'Mumbai', 30.8, 28.3, 33.6, 2023),
    (42, '2023-06-01', 'Mumbai', 30.4, 27.8, 33.7, 2023),
    (43, '2023-07-01', 'Mumbai', 27.8, 25.3, 29.4, 2023),
    (44, '2023-08-01', 'Mumbai', 28.6, 26.3, 30.8, 2023),
    (45, '2023-09-01', 'Mumbai', 28.2, 25.2, 31.0, 2023),
    (46, '2023-10-01', 'Mumbai', 30.2, 25.8, 34.5, 2023),
    (47, '2023-11-01', 'Mumbai', 29.4, 24.3, 34.4, 2023),
    (48, '2023-12-01', 'Mumbai', 27.9, 22.8, 32.9, 2023),
    (49, '2024-01-01', 'Mumbai', 26.3, 19.9, 31.3, 2024),
    (50, '2024-02-01', 'Mumbai', 27.1, 20.6, 32.6, 2024);

INSERT INTO city_weather_details
    (observation_id, rainfall_mm, wind_speed_kmh, pressure_hpa, sunshine_seconds, rainy_day)
VALUES
    (1,  0.0,    NULL, 1013.4, 13800, 0),
    (2,  0.0,    NULL, 1012.7, 11220, 0),
    (3,  0.0,    NULL, 1011.2, 12900, 0),
    (4,  0.0,    NULL, 1009.6, 14220, 0),
    (5,  0.0,    NULL, 1007.3, 15960, 0),
    (6,  525.0,  NULL, 1003.7, 8340,  1),
    (7,  1501.9, NULL, 1003.2, 4620,  1),
    (8,  826.5,  NULL, 1003.3, 2760,  1),
    (9,  320.0,  NULL, 1005.6, 7080,  1),
    (10, 224.0,  NULL, 1007.3, 7920,  1),
    (11, 0.0,    NULL, 1011.8, 12720, 0),
    (12, 25.0,   NULL, 1012.0, 11400, 1),
    (13, 1.0,    NULL, 1011.1, 11100, 1),
    (14, 0.0,    NULL, 1012.1, 11280, 0),
    (15, 0.0,    NULL, 1010.0, 13200, 0),
    (16, 0.0,    NULL, 1009.1, 13620, 0),
    (17, 154.4,  NULL, 1005.5, 12000, 1),
    (18, 317.0,  NULL, 1005.3, 6360,  1),
    (19, 773.9,  NULL, 1003.8, 4800,  1),
    (20, 295.1,  NULL, 1006.3, 5520,  1),
    (21, 436.9,  NULL, 1005.1, 5820,  1),
    (22, 31.8,   NULL, 1008.6, 13620, 1),
    (23, 50.1,   NULL, 1009.2, 12720, 1),
    (24, 103.3,  NULL, 1013.3, 10080, 1),
    (25, 9.6,    NULL, 1012.9, 11940, 1),
    (26, 0.0,    NULL, 1011.3, 14220, 0),
    (27, 0.1,    NULL, 1008.9, 9240,  1),
    (28, 0.0,    NULL, 1008.0, 12120, 0),
    (29, 7.0,    NULL, 1005.7, 13080, 1),
    (30, 298.3,  NULL, 1004.4, 7860,  1),
    (31, 1185.2, NULL, 1004.0, 3060,  1),
    (32, 550.9,  NULL, 1004.2, 5160,  1),
    (33, 528.4,  NULL, 1006.6, 5700,  1),
    (34, 165.5,  NULL, 1009.8, 11700, 1),
    (35, 0.0,    NULL, 1011.7, 12180, 0),
    (36, 6.2,    NULL, 1011.4, 10680, 1),
    (37, 0.0,    NULL, 1013.4, 11520, 0),
    (38, 0.0,    NULL, 1012.4, 13980, 0),
    (39, 21.0,   NULL, 1011.2, 12120, 1),
    (40, 15.3,   NULL, 1009.0, 14220, 1),
    (41, 0.6,    NULL, 1008.8, 17220, 1),
    (42, 561.1,  NULL, 1005.7, 11460, 1),
    (43, 1768.9, NULL, 1004.7, 1680,  1),
    (44, 187.3,  NULL, 1007.9, 7140,  1),
    (45, 483.8,  NULL, 1006.6, 6660,  1),
    (46, 13.0,   NULL, 1011.0, 10200, 1),
    (47, 7.1,    NULL, 1011.7, 11040, 1),
    (48, 0.0,    NULL, 1012.3, 10140, 0),
    (49, 1.1,    NULL, 1013.2, 12240, 1),
    (50, 0.0,    NULL, 1013.5, 14700, 0);

CREATE INDEX idx_temperature_city_date
ON city_daily_temperature (city, observation_date);

CREATE INDEX idx_weather_details_rainy_day
ON city_weather_details (rainy_day);

CREATE VIEW mumbai_rainy_months AS
SELECT
    t.observation_date,
    t.observation_year,
    t.average_temp_c,
    t.max_temp_c,
    d.rainfall_mm,
    d.pressure_hpa
FROM city_daily_temperature AS t
JOIN city_weather_details AS d
    ON d.observation_id = t.observation_id
WHERE t.city = 'Mumbai'
  AND d.rainy_day = 1;


SELECT
    (SELECT COUNT(*) FROM city_daily_temperature) AS temperature_rows,
    (SELECT COUNT(*) FROM city_weather_details) AS details_rows;


SELECT observation_date, city, average_temp_c, min_temp_c, max_temp_c
FROM city_daily_temperature
ORDER BY observation_date
LIMIT 10;


SELECT
    t.observation_year,
    COUNT(*) AS months_recorded,
    ROUND(AVG(t.average_temp_c), 1) AS average_temperature_c,
    ROUND(MAX(t.max_temp_c), 1) AS highest_max_temperature_c,
    ROUND(SUM(d.rainfall_mm), 1) AS total_rainfall_mm
FROM city_daily_temperature AS t
JOIN city_weather_details AS d
    ON d.observation_id = t.observation_id
GROUP BY t.observation_year
ORDER BY t.observation_year;


SELECT *
FROM mumbai_rainy_months
ORDER BY observation_date
LIMIT 10;