import pandas as pd


class DataUnavailableError(Exception):
    """Raised when the weather file / station data cannot be found."""


class InvalidSensorValueError(Exception):
    """Raised when a sensor reading is missing or physically impossible."""


VALID_RANGE = {                       # physically possible limits
    "temperature": (-10, 55),         # degree C
    "humidity":    (0, 100),          # %
    "wind_speed":  (0, 150),          # km/h
}


def load_station(path, station):
    """Load the daily readings of one weather station (mandal) from a CSV file."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise DataUnavailableError(f"Weather file not found: {path}")
    df = df[df["Mandal"] == station].reset_index(drop=True)
    if df.empty:
        raise DataUnavailableError(f"No data available for station '{station}'")
    return df


def validate(sensor, value):
    """Check one reading; raise InvalidSensorValueError if it is bad."""
    if pd.isna(value):
        raise InvalidSensorValueError(f"{sensor} reading missing (sensor / communication failure)")
    low, high = VALID_RANGE[sensor]
    if not low <= value <= high:
        raise InvalidSensorValueError(f"{sensor} value {value} outside valid range {low} to {high}")
    return float(value)


def read_sensor(df, column, sensor, day):
    """Read the value of one sensor for a given day index."""
    try:
        value = df.loc[day, column]
    except KeyError:
        raise DataUnavailableError(f"No reading available for day index {day}")
    return validate(sensor, value)
