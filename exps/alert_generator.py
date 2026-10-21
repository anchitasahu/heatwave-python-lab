THRESHOLDS = {                  # predefined warning limits
    "temperature": 41,          # degree C
    "humidity":    80,          # %
    "wind_speed":  20,          # km/h
}
UNITS = {"temperature": "C", "humidity": "%", "wind_speed": "km/h"}


def generate_alert(sensor, value, date):
    """Return a warning message if the value exceeds its threshold, else None."""
    limit = THRESHOLDS[sensor]
    unit = UNITS[sensor]
    if value > limit:
        return f"WARNING: {sensor} {value}{unit} exceeds limit {limit}{unit} on {date}"
    return None
