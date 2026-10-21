import pandas as pd

DATA = "datasets/"

class CityHeat:
    def __init__(self, city, temperatures=None):
        self.city = city

        if temperatures is None:
            self.temperatures = []
        else:
            self.temperatures = temperatures

        self.alert = "NONE"

    def add_reading(self, value):
        self.temperatures.append(value)

    def average(self):
        return round(sum(self.temperatures) / len(self.temperatures), 2)

    def hot_days(self, limit=40):
        hot = []
        for value in self.temperatures:
            if value >= limit:
                hot.append(value)
        return hot

    def show(self):
        print(self.city,
              "| days:", len(self.temperatures),
              "| avg:", self.average(),
              "| max:", max(self.temperatures),
              "| hot days:", len(self.hot_days()),
              "| alert:", self.alert)


def get_may_temperatures(file_name, date_format="%d-%m-%Y"):
    df = pd.read_csv(DATA + file_name)
    df["time"] = pd.to_datetime(df["time"], format=date_format)

    may_data = df[
        (df["time"] >= "2022-05-01") &
        (df["time"] <= "2022-05-31")
    ]

    return may_data["tmax"].dropna().tolist()


cities = []

cities.append(CityHeat("Delhi",
                       get_may_temperatures("ds03_city_tmax_delhi.csv")))
cities.append(CityHeat("Lucknow",
                       get_may_temperatures("ds04_city_tmax_lucknow.csv")))
cities.append(CityHeat("Chennai",
                       get_may_temperatures("ds02_city_tmax_chennai.csv")))
cities.append(CityHeat("Mumbai",
                       get_may_temperatures("ds05_city_tmax_mumbai.csv")))
cities.append(CityHeat("Bengaluru",
                       get_may_temperatures("ds01_city_tmax_bangalore.csv")))
cities.append(CityHeat("Bhubaneswar",
                       get_may_temperatures(
                           "ds06_city_weather_bhubaneswar.csv",
                           "%Y-%m-%d")))

print("=== Cities ===")
for city in cities:
    city.show()

delhi = cities[0].temperatures

print("\n=== List operations on Delhi ===")
print("First 7:", delhi[:7])
print("Length:", len(delhi))
print("Maximum:", max(delhi))
print("Minimum:", min(delhi))

hottest = max(delhi)
print("Index of hottest:", delhi.index(hottest))
print("Number of days >= 40:", len([x for x in delhi if x >= 40]))

delhi.append(41.5)
delhi.insert(0, 39.9)
print("Length after append and insert:", len(delhi))

delhi.remove(39.9)
removed = delhi.pop()
print("Popped value:", removed)

sorted_values = sorted(delhi, reverse=True)
print("Top 5:", sorted_values[:5])

print("\n=== Sort cities by average ===")
cities.sort(key=lambda x: x.average(), reverse=True)

for city in cities:
    print(city.city, city.average())

print("\n=== Updating alerts ===")
for city in cities:
    number_of_hot_days = len(city.hot_days())

    if number_of_hot_days >= 10:
        city.alert = "HEAT WATCH"
    elif number_of_hot_days > 0:
        city.alert = "ADVISORY"

for city in cities:
    city.show()

hot_cities = []
for city in cities:
    if len(city.hot_days()) > 0:
        hot_cities.append(city.city)

print("Cities having at least one 40 C day:", hot_cities)
