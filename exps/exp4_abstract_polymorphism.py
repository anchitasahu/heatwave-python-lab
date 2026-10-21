from abc import ABC, abstractmethod
import pandas as pd

DATA = "datasets/"


class ClimateAnalyzer(ABC):                     
    def __init__(self, name, file):
        self.name = name
        self.df = pd.read_csv(DATA + file)

    @abstractmethod
    def analyze(self):                           
        pass

    def report(self):                           
        print(f"[{self.name}]  rows loaded = {len(self.df)}")
        print("   ->", self.analyze())


class TemperatureAnalyzer(ClimateAnalyzer):     
    def analyze(self):
        t = self.df["tmax"].dropna()
        return (f"Delhi 1990-2022: hottest Tmax = {t.max()} C, "
                f"{(t >= 45).sum()} days >= 45 C, {(t >= 40).sum()} days >= 40 C")


class RainfallAnalyzer(ClimateAnalyzer):    
    def analyze(self):
        yearly = self.df.dropna(subset=["ANNUAL"]).groupby("SUBDIVISION")["ANNUAL"].mean()
        return (f"Driest subdivision  = {yearly.idxmin()} ({yearly.min():.0f} mm/yr); "
                f"wettest = {yearly.idxmax()} ({yearly.max():.0f} mm/yr)")


class AirQualityAnalyzer(ClimateAnalyzer):   
    def analyze(self):
        c = self.df.groupby("city")[["AQI", "temperature_2m"]].mean()
        return (f"Hottest city (Apr-Jul 2025) = {c['temperature_2m'].idxmax()} "
                f"({c['temperature_2m'].max():.1f} C); worst AQI = {c['AQI'].idxmax()} "
                f"({c['AQI'].max():.0f})")


class HumidityAnalyzer(ClimateAnalyzer):   
    def analyze(self):
        h = self.df["humidity"]
        return f"Delhi 2013-2017: mean humidity = {h.mean():.1f}%, minimum = {h.min():.1f}%"


class RegionAnalyzer(ClimateAnalyzer):   
    def analyze(self):
        r = self.df.groupby("region")["tmax_c"].max()
        return (f"2024 peak Tmax by region -> hottest: {r.idxmax()} ({r.max():.1f} C), "
                f"coolest: {r.idxmin()} ({r.min():.1f} C)")


print("=== Concrete analyzers: instantiation succeeds ===")
analyzers = [
    TemperatureAnalyzer("Temperature",  "ds03_city_tmax_delhi.csv"),
    RainfallAnalyzer("Rainfall",        "ds25_imd_rainfall_1901_2015.csv"),
    AirQualityAnalyzer("Air Quality",   "ds24_aqi_weather_dashboard.csv"),
    HumidityAnalyzer("Humidity",        "ds17_delhi_climate_train.csv"),
    RegionAnalyzer("Regional Climate",  "ds36_imd_gridded_tmax_2024.csv"),
]
print("\n=== Polymorphism: same report() call, different analyze() methods ===")
for a in analyzers:
    a.report()

print("\n=== Abstract base: instantiation raises TypeError ===")
try:
    ClimateAnalyzer("test", "ds03_city_tmax_delhi.csv")
except TypeError as e:
    print("Caught expected TypeError:", e)
