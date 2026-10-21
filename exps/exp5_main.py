import threading
import time
import pandas as pd

from exps.weather_collector import (load_station, read_sensor, validate,
                               DataUnavailableError, InvalidSensorValueError)
from exps.alert_generator import generate_alert

DATA = "datasets/"
FILE = DATA + "ds44_telangana_aws_may_2022.csv"
STATION = "Wanaparthy"
DAYS = 15

lock = threading.Lock()        
summary = {}                 

print("=== Part 1: unavailable weather data ===")
try:
    load_station(DATA + "ds99_not_available.csv", STATION)
except DataUnavailableError as e:
    print("Handled DataUnavailableError ->", e)
else:
    print("File loaded successfully")
finally:
    print("finally block: data-loading attempt finished\n")

try:
    load_station(FILE, "Atlantis")
except DataUnavailableError as e:
    print("Handled DataUnavailableError ->", e, "\n")


def monitor(df, sensor, column):
    valid = warnings = errors = 0
    for day in range(DAYS):
        date = df.loc[day, "Date"]
        try:
            value = read_sensor(df, column, sensor, day)          
            valid += 1
            alert = generate_alert(sensor, value, date)       
            if alert:
                warnings += 1
                with lock:
                    print(f"[{sensor:11}] {alert}")
        except InvalidSensorValueError as e:
            errors += 1
            with lock:
                print(f"[{sensor:11}] ERROR on {date}: {e}")
        time.sleep(0.01)                                       
    summary[sensor] = [valid, warnings, errors]


print(f"=== Part 2: concurrent monitoring of station '{STATION}' (first {DAYS} days of May 2022) ===")
try:
    station_df = load_station(FILE, STATION)
    threads = [
        threading.Thread(target=monitor, args=(station_df, "temperature", "Max Temp (°C)")),
        threading.Thread(target=monitor, args=(station_df, "humidity",    "Max Humidity (%)")),
        threading.Thread(target=monitor, args=(station_df, "wind_speed",  "Max Wind Speed (Kmph)")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()                                                 
except DataUnavailableError as e:
    print("Monitoring stopped:", e)

print("\n=== Monitoring summary ===")
print(f"{'Sensor':12} {'Valid':>6} {'Warnings':>9} {'Errors':>7}")
for sensor in ["temperature", "humidity", "wind_speed"]:
    v, w, e = summary[sensor]
    print(f"{sensor:12} {v:6} {w:9} {e:7}")

print("\n=== Part 3: invalid sensor value found in DS20 ===")
try:
    big = pd.read_csv(DATA + "ds20_north_india_stations_weather.csv",
                      usecols=["date_of_record", "station_name", "max_temp"])
    bad = big[big["max_temp"] > 55].iloc[0]
    print(f"Reading found: {bad['station_name']} on {str(bad['date_of_record'])[:10]} -> {bad['max_temp']} C")
    validate("temperature", bad["max_temp"])
except InvalidSensorValueError as e:
    print("Handled InvalidSensorValueError ->", e)
finally:
    print("Quality check finished")
