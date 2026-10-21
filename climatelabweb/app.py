"""Dependency-free web backend for the six climate intelligence experiments."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "datasets"
WEB_DIR = Path(__file__).resolve().parent
LOG = logging.getLogger("climate-dashboard")

CITY_DATASETS = {
    "Bengaluru": ("ds01_city_tmax_bangalore.csv", "%d-%m-%Y"),
    "Chennai": ("ds02_city_tmax_chennai.csv", "%d-%m-%Y"),
    "Delhi": ("ds03_city_tmax_delhi.csv", "%d-%m-%Y"),
    "Lucknow": ("ds04_city_tmax_lucknow.csv", "%d-%m-%Y"),
    "Mumbai": ("ds05_city_tmax_mumbai.csv", "%d-%m-%Y"),
    "Bhubaneswar": ("ds06_city_weather_bhubaneswar.csv", "%Y-%m-%d"),
}
HISTORIC_CITIES = {
    "Delhi": CITY_DATASETS["Delhi"][0],
    "Lucknow": CITY_DATASETS["Lucknow"][0],
    "Chennai": CITY_DATASETS["Chennai"][0],
    "Mumbai": CITY_DATASETS["Mumbai"][0],
}
TELANGANA_FILE = "ds44_telangana_aws_may_2022.csv"
SENSOR_FIELDS = {
    "temperature": ("Max Temp (°C)", -10.0, 55.0, 41.0, "°C"),
    "humidity": ("Max Humidity (%)", 0.0, 100.0, 80.0, "%"),
    "wind_speed": ("Max Wind Speed (Kmph)", 0.0, 150.0, 20.0, "km/h"),
}


def read_rows(filename: str) -> list[dict[str, str]]:
    """Read a project-owned CSV file without relying on third-party packages."""
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def numeric(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def rounded(value: float | None, places: int = 1) -> float | None:
    return round(value, places) if value is not None else None


def parse_date(value: str) -> datetime | None:
    cleaned = value.strip().replace(" ", "")
    for date_format in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(cleaned, date_format)
        except ValueError:
            continue
    return None


def heat_level(temperature: float) -> str:
    if temperature >= 47:
        return "SEVERE HEATWAVE"
    if temperature >= 45:
        return "HEATWAVE"
    if temperature >= 40:
        return "HEAT WATCH"
    return "NORMAL"


def city_may_series(city: str) -> list[dict[str, object]]:
    filename, _ = CITY_DATASETS[city]
    observations = []
    for row in read_rows(filename):
        day = parse_date(row.get("time", ""))
        temperature = numeric(row, "tmax")
        if day and day.year == 2022 and day.month == 5 and temperature is not None:
            observations.append({"date": day.strftime("%d %b"), "temperature": temperature})
    return observations


def may_city_summaries() -> list[dict[str, object]]:
    summaries = []
    for city in CITY_DATASETS:
        series = city_may_series(city)
        values = [item["temperature"] for item in series]
        if not values:
            continue
        hot_days = sum(value >= 40 for value in values)
        summaries.append(
            {
                "city": city,
                "days": len(values),
                "average": rounded(sum(values) / len(values), 2),
                "maximum": rounded(max(values), 1),
                "minimum": rounded(min(values), 1),
                "hot_days": hot_days,
                "alert": "HEAT WATCH" if hot_days >= 10 else "ADVISORY" if hot_days else "NONE",
                "series": series,
            }
        )
    return summaries


def top_historic_days(city: str, limit: int) -> list[dict[str, object]]:
    rows = read_rows(HISTORIC_CITIES[city])
    valid_rows = []
    for row in rows:
        maximum = numeric(row, "tmax")
        minimum = numeric(row, "tmin")
        day = parse_date(row.get("time", ""))
        if maximum is None or minimum is None or day is None:
            continue
        valid_rows.append(
            {
                "city": city,
                "date": day.strftime("%d %b %Y"),
                "maximum": maximum,
                "minimum": minimum,
                "range": rounded(maximum - minimum, 1),
                "rainfall": numeric(row, "prcp") or 0.0,
                "category": heat_level(maximum),
                "_sort": day,
            }
        )
    valid_rows.sort(key=lambda item: item["maximum"], reverse=True)
    hottest = valid_rows[:limit]
    for item in hottest:
        item.pop("_sort")
    return hottest


def dataset_catalog() -> list[dict[str, str]]:
    return read_rows("00_dataset_catalog.csv")


def overview() -> dict[str, object]:
    cities = may_city_summaries()
    hottest = []
    for city in HISTORIC_CITIES:
        hottest.extend(top_historic_days(city, 1))
    hottest.sort(key=lambda item: item["maximum"], reverse=True)
    catalog = dataset_catalog()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_mode": "archived CSV snapshot",
        "period": "May 2022",
        "dataset_count": len(catalog),
        "city_count": len(cities),
        "hot_days": sum(int(city["hot_days"]) for city in cities),
        "hottest_cities": sorted(cities, key=lambda item: item["average"], reverse=True),
        "historic_extremes": hottest[:5],
    }


def experiment_one(query: dict[str, list[str]]) -> dict[str, object]:
    city = query.get("city", ["Delhi"])[0]
    if city not in HISTORIC_CITIES:
        raise ValueError("Experiment 1 supports Delhi, Lucknow, Chennai, and Mumbai.")
    try:
        limit = int(query.get("limit", ["5"])[0])
    except ValueError as error:
        raise ValueError("Limit must be a whole number from 1 to 20.") from error
    if not 1 <= limit <= 20:
        raise ValueError("Limit must be a whole number from 1 to 20.")
    return {
        "experiment": 1,
        "title": "Heatwave station objects",
        "city": city,
        "dataset": HISTORIC_CITIES[city],
        "records": top_historic_days(city, limit),
        "total_objects": limit,
        "valid_temperature_range_c": [-10, 55],
        "thresholds": {"heat_watch": 40, "heatwave": 45, "severe_heatwave": 47},
    }


def experiment_two() -> dict[str, object]:
    return {
        "experiment": 2,
        "title": "May city comparison",
        "cities": may_city_summaries(),
        "threshold_c": 40,
        "period": "01–31 May 2022",
    }


@lru_cache(maxsize=1)
def realtime_location_snapshot() -> tuple[list[dict[str, str]], dict[str, int]]:
    latest: dict[str, dict[str, str]] = {}
    old_name_rows = 0
    snapshot_epoch = 0.0
    for row in read_rows("ds19_realtime_india_543_locations.csv"):
        name = row.get("location_name", "").strip()
        if not name:
            continue
        if row.get("region", "").strip() == "Orissa":
            old_name_rows += 1
        epoch = numeric(row, "last_updated_epoch") or 0
        snapshot_epoch = max(snapshot_epoch, epoch)
        prior_epoch = numeric(latest.get(name, {}), "last_updated_epoch") or 0
        if name not in latest or epoch >= prior_epoch:
            latest[name] = row
    locations = []
    for row in latest.values():
        epoch = numeric(row, "last_updated_epoch")
        source_time = row.get("last_updated", "").strip()
        if epoch is not None:
            source_time = datetime.fromtimestamp(
                epoch, tz=timezone(timedelta(hours=5, minutes=30))
            ).strftime("%d %b %Y, %H:%M IST")
        locations.append(
            {
                "name": row.get("location_name", "").strip(),
                "region": row.get("region", "").strip().replace("Orissa", "Odisha"),
                "temperature": row.get("temperature_celsius", ""),
                "humidity": row.get("humidity", ""),
                "condition": row.get("condition_text", ""),
                "last_updated": source_time,
            }
        )
    locations.sort(key=lambda item: item["name"].casefold())
    names = [item["name"] for item in locations]
    metadata = {
        "location_count": len(locations),
        "old_region_rows": old_name_rows,
        "longest_location": max(names, key=len) if names else "",
        "pur_count": sum("pur" in name.casefold() for name in names),
        "snapshot_time": (
            datetime.fromtimestamp(
                snapshot_epoch, tz=timezone(timedelta(hours=5, minutes=30))
            ).strftime("%d %b %Y, %H:%M IST")
            if snapshot_epoch
            else "Timestamp unavailable"
        ),
    }
    return locations, metadata


def experiment_three(query: dict[str, list[str]]) -> dict[str, object]:
    locations, metadata = realtime_location_snapshot()
    search = query.get("q", [""])[0].strip().casefold()
    if len(search) > 80:
        raise ValueError("Location search must be 80 characters or fewer.")
    mode = query.get("mode", ["all"])[0]
    if mode not in {"all", "starts-ban", "contains-pur"}:
        raise ValueError("Unknown location filter.")
    matches = []
    for location in locations:
        name = location["name"]
        if search and search not in name.casefold() and search not in location["region"].casefold():
            continue
        if mode == "starts-ban" and not name.casefold().startswith("ban"):
            continue
        if mode == "contains-pur" and "pur" not in name.casefold():
            continue
        matches.append(location)
    page = max(1, int(query.get("page", ["1"])[0]))
    page_size = 20
    return {
        "experiment": 3,
        "title": "Location strings & heat alerts",
        "metadata": metadata,
        "query": search,
        "mode": mode,
        "total_matches": len(matches),
        "page": page,
        "page_size": page_size,
        "locations": matches[(page - 1) * page_size : page * page_size],
        "alerts": top_historic_days("Delhi", 3) + top_historic_days("Lucknow", 3),
        "snapshot_time": metadata["snapshot_time"],
    }


def experiment_four(query: dict[str, list[str]]) -> dict[str, object]:
    analyzer = query.get("analyzer", ["temperature"])[0]
    if analyzer == "temperature":
        rows = read_rows("ds03_city_tmax_delhi.csv")
        by_year: dict[str, list[float]] = defaultdict(list)
        values = []
        for row in rows:
            value = numeric(row, "tmax")
            day = parse_date(row.get("time", ""))
            if value is not None and day:
                values.append(value)
                by_year[str(day.year)].append(value)
        series = [
            {"label": year, "value": rounded(max(year_values), 1)}
            for year, year_values in sorted(by_year.items())
        ]
        return {
            "experiment": 4,
            "analyzer": analyzer,
            "title": "Delhi maximum temperature",
            "dataset": "ds03_city_tmax_delhi.csv",
            "rows_loaded": len(rows),
            "summary": [
                {"label": "Record high", "value": f"{max(values):.1f} °C"},
                {"label": "Days ≥ 40 °C", "value": str(sum(value >= 40 for value in values))},
                {"label": "Days ≥ 45 °C", "value": str(sum(value >= 45 for value in values))},
            ],
            "series": series,
            "chart_title": "Annual peak Tmax · 1990–2022",
            "unit": "°C",
        }
    if analyzer == "rainfall":
        rows = read_rows("ds25_imd_rainfall_1901_2015.csv")
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            value = numeric(row, "ANNUAL")
            if value is not None:
                grouped[row["SUBDIVISION"].strip()].append(value)
        means = [
            {"label": name, "value": sum(values) / len(values)}
            for name, values in grouped.items()
            if values
        ]
        means.sort(key=lambda item: item["value"])
        return {
            "experiment": 4,
            "analyzer": analyzer,
            "title": "Subdivision rainfall",
            "dataset": "ds25_imd_rainfall_1901_2015.csv",
            "rows_loaded": len(rows),
            "summary": [
                {"label": "Driest subdivision", "value": f"{means[0]['label']} · {means[0]['value']:.0f} mm/yr"},
                {"label": "Wettest subdivision", "value": f"{means[-1]['label']} · {means[-1]['value']:.0f} mm/yr"},
            ],
            "series": [{"label": item["label"], "value": rounded(item["value"], 1)} for item in means],
            "chart_title": "Mean annual rainfall by subdivision",
            "unit": "mm/yr",
        }
    if analyzer == "air-quality":
        rows = read_rows("ds24_aqi_weather_dashboard.csv")
        grouped: dict[str, list[tuple[float, float | None]]] = defaultdict(list)
        for row in rows:
            aqi = numeric(row, "AQI")
            temperature = numeric(row, "temperature_2m")
            if aqi is not None:
                grouped[row["city"].strip()].append((aqi, temperature))
        cities = []
        for name, values in grouped.items():
            aqi_values = [item[0] for item in values]
            temperature_values = [item[1] for item in values if item[1] is not None]
            cities.append(
                {
                    "label": name,
                    "value": sum(aqi_values) / len(aqi_values),
                    "temperature": (
                        sum(temperature_values) / len(temperature_values)
                        if temperature_values
                        else None
                    ),
                }
            )
        cities.sort(key=lambda item: item["value"], reverse=True)
        hottest = max((item for item in cities if item["temperature"] is not None), key=lambda item: item["temperature"])
        return {
            "experiment": 4,
            "analyzer": analyzer,
            "title": "Air quality & weather",
            "dataset": "ds24_aqi_weather_dashboard.csv",
            "rows_loaded": len(rows),
            "summary": [
                {"label": "Highest mean AQI", "value": f"{cities[0]['label']} · {cities[0]['value']:.0f}"},
                {"label": "Warmest city", "value": f"{hottest['label']} · {hottest['temperature']:.1f} °C"},
            ],
            "series": [{"label": item["label"], "value": rounded(item["value"], 1)} for item in cities[:12]],
            "chart_title": "Cities with highest mean AQI",
            "unit": "AQI",
        }
    if analyzer == "humidity":
        rows = read_rows("ds17_delhi_climate_train.csv")
        by_year: dict[str, list[float]] = defaultdict(list)
        values = []
        for row in rows:
            humidity = numeric(row, "humidity")
            day = parse_date(row.get("date", ""))
            if humidity is not None:
                values.append(humidity)
                if day:
                    by_year[str(day.year)].append(humidity)
        return {
            "experiment": 4,
            "analyzer": analyzer,
            "title": "Delhi humidity",
            "dataset": "ds17_delhi_climate_train.csv",
            "rows_loaded": len(rows),
            "summary": [
                {"label": "Mean humidity", "value": f"{sum(values) / len(values):.1f}%"},
                {"label": "Minimum humidity", "value": f"{min(values):.1f}%"},
            ],
            "series": [
                {"label": year, "value": rounded(sum(year_values) / len(year_values), 1)}
                for year, year_values in sorted(by_year.items())
            ],
            "chart_title": "Mean humidity by year · 2013–2017",
            "unit": "%",
        }
    if analyzer == "regions":
        rows = read_rows("ds36_imd_gridded_tmax_2024.csv")
        maxima: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            value = numeric(row, "tmax_c")
            if value is not None:
                maxima[row["region"].strip()].append(value)
        series = [
            {"label": region, "value": max(values)}
            for region, values in maxima.items()
        ]
        series.sort(key=lambda item: item["value"], reverse=True)
        return {
            "experiment": 4,
            "analyzer": analyzer,
            "title": "Regional climate extremes",
            "dataset": "ds36_imd_gridded_tmax_2024.csv",
            "rows_loaded": len(rows),
            "summary": [
                {"label": "Hottest region", "value": f"{series[0]['label']} · {series[0]['value']:.1f} °C"},
                {"label": "Coolest region", "value": f"{series[-1]['label']} · {series[-1]['value']:.1f} °C"},
            ],
            "series": [{"label": item["label"], "value": rounded(item["value"], 1)} for item in series],
            "chart_title": "Peak Tmax by region · 2024",
            "unit": "°C",
        }
    raise ValueError("Choose temperature, rainfall, air-quality, humidity, or regions.")


def station_rows(station: str) -> list[dict[str, str]]:
    rows = [row for row in read_rows(TELANGANA_FILE) if row.get("Mandal", "").strip() == station]
    if not rows:
        raise ValueError(f"No observations found for station {station!r}.")
    rows.sort(key=lambda row: parse_date(row.get("Date", "")) or datetime.min)
    return rows


def inspect_sensor(
    rows: list[dict[str, str]], sensor: str, days: int
) -> dict[str, object]:
    field, low, high, threshold, unit = SENSOR_FIELDS[sensor]
    readings = []
    warnings = []
    errors = []
    valid = 0
    for row in rows[:days]:
        value = numeric(row, field)
        date = row.get("Date", "")
        if value is None:
            errors.append({"date": date, "message": f"{sensor.replace('_', ' ')} reading missing"})
            readings.append({"date": date, "value": None})
            continue
        if not low <= value <= high:
            errors.append(
                {"date": date, "message": f"{sensor.replace('_', ' ')} value {value:g} outside valid range {low:g} to {high:g}"}
            )
            readings.append({"date": date, "value": None})
            continue
        valid += 1
        readings.append({"date": date, "value": rounded(value, 1)})
        if value > threshold:
            warnings.append(
                {
                    "date": date,
                    "value": rounded(value, 1),
                    "message": f"{sensor.replace('_', ' ')} {value:g}{unit} exceeds limit {threshold:g}{unit}",
                }
            )
    return {
        "sensor": sensor,
        "valid": valid,
        "warnings": warnings,
        "errors": errors,
        "readings": readings,
        "threshold": threshold,
        "unit": unit,
    }


@lru_cache(maxsize=1)
def first_faulty_north_india_reading() -> dict[str, object] | None:
    path = DATA_DIR / "ds20_north_india_stations_weather.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            value = numeric(row, "max_temp")
            if value is not None and value > 55:
                return {
                    "station": row.get("station_name", ""),
                    "date": row.get("date_of_record", ""),
                    "temperature": value,
                    "accepted": False,
                    "reason": f"temperature value {value:g} outside valid range -10 to 55",
                }
    return None


def experiment_five(query: dict[str, list[str]]) -> dict[str, object]:
    station = query.get("station", ["Wanaparthy"])[0].strip()
    if not station:
        raise ValueError("Choose a station.")
    try:
        days = int(query.get("days", ["15"])[0])
    except ValueError as error:
        raise ValueError("Days must be a whole number from 1 to 31.") from error
    if not 1 <= days <= 31:
        raise ValueError("Days must be a whole number from 1 to 31.")
    rows = station_rows(station)
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="sensor") as pool:
        sensor_results = list(
            pool.map(lambda sensor: inspect_sensor(rows, sensor, days), SENSOR_FIELDS)
        )
    sensors = {item["sensor"]: item for item in sensor_results}
    return {
        "experiment": 5,
        "title": "Concurrent sensor monitoring",
        "dataset": TELANGANA_FILE,
        "station": station,
        "days_requested": days,
        "sensors": sensors,
        "faulty_reading": first_faulty_north_india_reading(),
        "data_checks": ["missing values", "temperature -10–55 °C", "humidity 0–100%", "wind 0–150 km/h"],
        "thresholds": {"temperature": 41, "humidity": 80, "wind_speed": 20},
    }


def experiment_six(query: dict[str, list[str]]) -> dict[str, object]:
    selected = query.get("station", ["Adilabad Rural,Wanaparthy"])[0]
    requested = [name.strip() for name in selected.split(",") if name.strip()]
    if not requested or len(requested) > 6:
        raise ValueError("Choose between one and six Telangana stations.")
    summaries = []
    for station in requested:
        rows = station_rows(station)
        complete = [
            row
            for row in rows
            if all(
                numeric(row, column) is not None
                for column in ("Max Temp (°C)", "Max Humidity (%)", "Max Wind Speed (Kmph)")
            )
        ]
        if not complete:
            raise ValueError(f"No complete temperature, humidity, and wind readings for {station}.")
        temperatures = [numeric(row, "Max Temp (°C)") for row in complete]
        humidities = [numeric(row, "Max Humidity (%)") for row in complete]
        winds = [numeric(row, "Max Wind Speed (Kmph)") for row in complete]
        alerts = sorted({heat_level(value) for value in temperatures if value is not None})
        summaries.append(
            {
                "station": station,
                "district": complete[0].get("District", ""),
                "days_observed": len(complete),
                "maximum_temperature_c": rounded(max(temperatures), 1),
                "mean_temperature_c": rounded(sum(temperatures) / len(temperatures), 1),
                "mean_humidity_percent": rounded(sum(humidities) / len(humidities), 1),
                "mean_wind_speed_kmh": rounded(sum(winds) / len(winds), 1),
                "total_rainfall_mm": rounded(sum(numeric(row, "Rain (mm)") or 0 for row in complete), 1),
                "alert_levels": alerts,
                "series": [
                    {
                        "date": row.get("Date", ""),
                        "temperature": numeric(row, "Max Temp (°C)"),
                        "humidity": numeric(row, "Max Humidity (%)"),
                        "wind_speed": numeric(row, "Max Wind Speed (Kmph)"),
                    }
                    for row in complete
                ],
                "fahrenheit_preview": [
                    rounded(value * 9 / 5 + 32, 1)
                    for value in temperatures[:5]
                    if value is not None
                ],
                "heat_monitor_readings": sum(
                    value >= 40 for value in temperatures if value is not None
                ),
                "total_temperature_c": rounded(sum(temperatures), 1),
            }
        )
    return {
        "experiment": 6,
        "title": "Climate intelligence summary",
        "dataset": TELANGANA_FILE,
        "period": "May 2022",
        "stations": summaries,
        "collection_concepts": ["list", "tuple", "set", "dictionary"],
    }


def api_response(
    request_path: str, query: dict[str, list[str]]
) -> tuple[dict[str, object], int]:
    try:
        if request_path == "/api/overview":
            payload = overview()
        elif request_path == "/api/experiments/1":
            payload = experiment_one(query)
        elif request_path == "/api/experiments/2":
            payload = experiment_two()
        elif request_path == "/api/experiments/3":
            payload = experiment_three(query)
        elif request_path == "/api/experiments/4":
            payload = experiment_four(query)
        elif request_path == "/api/experiments/5":
            payload = experiment_five(query)
        elif request_path == "/api/experiments/6":
            payload = experiment_six(query)
        elif request_path == "/api/stations":
            stations = sorted(
                {
                    row["Mandal"].strip()
                    for row in read_rows(TELANGANA_FILE)
                    if row.get("Mandal", "").strip()
                }
            )
            payload = {"stations": stations}
        elif request_path == "/api/catalog":
            payload = {"datasets": dataset_catalog()}
        else:
            return {"error": "API endpoint not found."}, 404
    except (ValueError, OSError, csv.Error, KeyError) as error:
        LOG.exception("Request failed for %s", request_path)
        return {"error": str(error)}, 400 if isinstance(error, ValueError) else 500
    return payload, 200


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "ClimateDashboard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html", "/styles.css", "/app.js"}:
            self.serve_static(parsed.path)
            return
        payload, status = api_response(parsed.path, parse_qs(parsed.query))
        self.send_json(payload, status=status)

    def serve_static(self, request_path: str) -> None:
        filename = "index.html" if request_path == "/" else request_path.lstrip("/")
        path = (WEB_DIR / filename).resolve()
        if path.parent != WEB_DIR.resolve() or not path.is_file():
            self.send_json({"error": "Static file not found."}, status=404)
            return
        content_type = "text/html; charset=utf-8" if path.suffix == ".html" else (
            "text/css; charset=utf-8" if path.suffix == ".css" else "text/javascript; charset=utf-8"
        )
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        LOG.info("%s - %s", self.address_string(), format_string % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the interactive climate experiments dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="TCP port to listen on (default: 8000).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    LOG.info("Climate dashboard ready at http://%s:%s", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Stopping climate dashboard.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
