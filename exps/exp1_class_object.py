import pandas as pd

DATA = "datasets/"


class HeatwaveStation:

    count = 0

    def __init__(self, city, date, tmax, tmin, rain):
        self.city = city
        self.date = date
        self.tmax = tmax
        self.tmin = tmin
        self.rain = rain

        HeatwaveStation.count += 1

    def show(self):
        print(self.city, self.date)
        print("Maximum temperature:", self.tmax)
        print("Minimum temperature:", self.tmin)
        print("Rainfall:", self.rain)

    def category(self):

        if self.tmax >= 47:
            return "SEVERE HEATWAVE"

        elif self.tmax >= 45:
            return "HEATWAVE"

        elif self.tmax >= 40:
            return "HEAT WATCH"

        else:
            return "NORMAL"

    @staticmethod
    def valid_temperature(t):
        if t >= -10 and t <= 55:
            return True
        else:
            return False

    @classmethod
    def total_objects(cls):
        return cls.count


def get_hottest(file, city):

    df = pd.read_csv(DATA + file)

    df["time"] = pd.to_datetime(
        df["time"],
        format="%d-%m-%Y"
    )

    df = df.dropna(
        subset=["tmax", "tmin"]
    )

    # Arrange temperatures from high to low
    df = df.sort_values(
        "tmax",
        ascending=False
    )

    stations = []

    # Take first two hottest days
    for i in range(2):

        row = df.iloc[i]

        obj = HeatwaveStation(
            city,
            row["time"].strftime("%d-%m-%Y"),
            row["tmax"],
            row["tmin"],
            row["prcp"]
        )

        stations.append(obj)

    return stations


# Creating objects using dataset

stations = []

stations = stations + get_hottest(
    "ds03_city_tmax_delhi.csv",
    "Delhi"
)

stations = stations + get_hottest(
    "ds04_city_tmax_lucknow.csv",
    "Lucknow"
)

stations = stations + get_hottest(
    "ds02_city_tmax_chennai.csv",
    "Chennai"
)

stations = stations + get_hottest(
    "ds05_city_tmax_mumbai.csv",
    "Mumbai"
)


print("Hottest days:")

for s in stations:

    s.show()

    print(
        "Category:",
        s.category()
    )

    print()


print(
    "Total objects:",
    HeatwaveStation.total_objects()
)

print(
    "Is 48.1 valid?",
    HeatwaveStation.valid_temperature(48.1)
)

print(
    "Is 99 valid?",
    HeatwaveStation.valid_temperature(99)
)