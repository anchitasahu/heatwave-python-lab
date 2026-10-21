import pandas as pd

DATA = "datasets/"

live = pd.read_csv(
    DATA + "ds19_realtime_india_543_locations.csv",
    usecols=["location_name", "region",
             "temperature_celsius", "last_updated"]
)

place = "   " + live.loc[0, "location_name"] + "   "
state = live.loc[0, "region"]
stamp = live.loc[0, "last_updated"]

print("=== String handling ===")
print("Original:", repr(place))
print("Length:", len(place))
print("After strip:", place.strip())
print("Upper:", place.strip().upper())
print("Lower:", place.strip().lower())
print("Title:", "new delhi".title())
print("Replace:", "Orissa".replace("Orissa", "Odisha"))
print("Concatenation:", place.strip() + ", " + state)
print("Repetition:", "-" * 30)

temperature = live.loc[0, "temperature_celsius"]
print(f"{place.strip()} ({state}) reported {temperature} C")

date_part, time_part = stamp.split(" ")
day, month, year = date_part.split("-")

print("Day:", day)
print("Month:", month)
print("Year:", year)
print("Time:", time_part)

iso_date = "-".join([year, month, day])
print("ISO date:", iso_date)

names = live["location_name"].str.strip().unique().tolist()

print("\nUnique locations:", len(names))

starting_ban = []
for name in names:
    if name.startswith("Ban"):
        starting_ban.append(name)

print("Names starting with Ban:", starting_ban[:6])

pur_count = 0
for name in names:
    if "pur" in name.lower():
        pur_count += 1

print("Names containing pur:", pur_count)

old_name_count = (live["region"] == "Orissa").sum()
print("Orissa rows:", old_name_count)

live["region"] = live["region"].str.replace("Orissa", "Odisha")
print("Odisha rows after replacement:",
      (live["region"] == "Odisha").sum())

longest_name = max(names, key=len)
print("Longest location:", longest_name)


class Location:
    def __init__(self, city, state):
        self.city = city.strip()
        self.state = state.strip()

    def label(self):
        return self.city.title() + ", " + self.state.upper()


class Observation(Location):
    def __init__(self, city, state, date, tmax, tmin):
        super().__init__(city, state)
        self.date = date
        self.tmax = tmax
        self.tmin = tmin

    def month_name(self):
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        month_number = int(self.date.split("-")[1])
        return months[month_number - 1]


class HeatAlert(Observation):
    def level(self):
        if self.tmax >= 47:
            return "SEVERE HEATWAVE"
        elif self.tmax >= 45:
            return "HEATWAVE"
        elif self.tmax >= 40:
            return "HEAT WATCH"
        else:
            return "NORMAL"

    def message(self):
        return (
            "ALERT | " + self.label() +
            " | " + self.date +
            " (" + self.month_name() + ")" +
            " | Tmax " + str(self.tmax) +
            " C, Tmin " + str(self.tmin) +
            " C | " + self.level()
        )


def get_top_days(file_name, city, state, n=3):
    df = pd.read_csv(DATA + file_name)
    df = df.dropna(subset=["tmax", "tmin"])
    df = df.nlargest(n, "tmax")

    alerts = []
    for _, row in df.iterrows():
        alerts.append(
            HeatAlert(city, state,
                      row["time"], row["tmax"], row["tmin"])
        )
    return alerts


print("\n=== Multilevel inheritance ===")

alerts = get_top_days(
    "ds03_city_tmax_delhi.csv", "delhi", "delhi"
)

alerts += get_top_days(
    "ds04_city_tmax_lucknow.csv",
    " lucknow ",
    "uttar pradesh"
)

for alert in alerts:
    print(alert.message())

print("\nHeatAlert is Observation:",
      issubclass(HeatAlert, Observation))

print("HeatAlert is Location:",
      issubclass(HeatAlert, Location))

print("MRO:",
      [cls.__name__ for cls in HeatAlert.__mro__])
