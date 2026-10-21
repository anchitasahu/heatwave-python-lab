from functools import reduce
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "datasets" / "ds44_telangana_aws_may_2022.csv"
LOCATIONS = ("Adilabad Rural", "Wanaparthy")
REPORT_PERIOD = "May 2022"
HEAT_MONITOR_LIMIT = 40


def alert_level(temperature):
    if temperature >= 47:
        return "SEVERE HEATWAVE"
    if temperature >= 45:
        return "HEATWAVE"
    if temperature >= HEAT_MONITOR_LIMIT:
        return "HEAT WATCH"
    return "NORMAL"


weather_data = pd.read_csv(
    DATA,
    usecols=[
        "District",
        "Mandal",
        "Date",
        "Rain (mm)",
        "Max Temp (°C)",
        "Max Humidity (%)",
        "Max Wind Speed (Kmph)",
    ],
)
weather_data = weather_data[
    weather_data["Mandal"].isin(LOCATIONS)
].dropna(subset=["Max Temp (°C)", "Max Humidity (%)", "Max Wind Speed (Kmph)"])

if weather_data.empty:
    raise ValueError(f"No weather observations found for {REPORT_PERIOD}.")

# List: daily temperature readings across the selected locations.
temperature_readings = weather_data["Max Temp (°C)"].astype(float).tolist()

# Tuple: station/location details for the selected city observations.
station_information = tuple(
    (mandal, district, "DS44 Telangana AWS")
    for mandal, district in weather_data[["Mandal", "District"]].drop_duplicates().itertuples(index=False, name=None)
)

# Set: unique alert categories present in the selected observations.
alert_levels = set(map(alert_level, temperature_readings))

# Dictionary: per-location weather summaries.
weather_information = {}
for mandal, station_data in weather_data.groupby("Mandal", sort=True):
    station_temperatures = station_data["Max Temp (°C)"].astype(float).tolist()
    weather_information[mandal] = {
        "days_observed": len(station_data),
        "maximum_temperature_c": max(station_temperatures),
        "mean_humidity_percent": station_data["Max Humidity (%)"].mean(),
        "mean_wind_speed_kmh": station_data["Max Wind Speed (Kmph)"].mean(),
        "total_rainfall_mm": station_data["Rain (mm)"].sum(),
        "alert_levels": sorted(set(map(alert_level, station_temperatures))),
    }

temperatures_fahrenheit = list(
    map(lambda celsius: round(celsius * 9 / 5 + 32, 1), temperature_readings)
)
heat_monitor_readings = list(
    filter(lambda celsius: celsius >= HEAT_MONITOR_LIMIT, temperature_readings)
)
total_temperature = reduce(
    lambda total, celsius: total + celsius,
    temperature_readings,
    0.0,
)

print("=== Climate Intelligence: Heatwave Monitoring Report ===")
print(f"Dataset: {DATA.name} | Period: {REPORT_PERIOD}")
print(f"Locations monitored: {', '.join(LOCATIONS)}")
print(f"Station information (tuple): {station_information}")
print(f"Unique alert levels (set): {', '.join(sorted(alert_levels))}")

print("\n=== Functional temperature analysis ===")
print(f"Temperature readings stored in list: {len(temperature_readings)}")
print("First 5 temperatures in Fahrenheit (map + lambda):", temperatures_fahrenheit[:5])
print(
    f"Readings >= {HEAT_MONITOR_LIMIT} C (filter): "
    f"{len(heat_monitor_readings)}; values: {[round(value, 1) for value in heat_monitor_readings]}"
)
print(f"Total temperature across readings (reduce): {total_temperature:.1f} C")

print("\n=== Per-location weather information (dictionary) ===")
for mandal, summary in weather_information.items():
    print(
        f"{mandal:16} | days: {summary['days_observed']:2} | "
        f"max: {summary['maximum_temperature_c']:.1f} C | "
        f"mean humidity: {summary['mean_humidity_percent']:.1f}% | "
        f"mean wind: {summary['mean_wind_speed_kmh']:.1f} km/h | "
        f"alerts: {', '.join(summary['alert_levels'])}"
    )

print("\nMonitoring rule: >= 40 C is flagged for heat monitoring (teaching threshold).")