import unittest

import app


class ExperimentDataTests(unittest.TestCase):
    def test_experiment_one_finds_delhi_record_high(self):
        result = app.experiment_one({"city": ["Delhi"], "limit": ["2"]})
        self.assertEqual(result["records"][0]["maximum"], 48.1)
        self.assertEqual(result["records"][0]["category"], "SEVERE HEATWAVE")

    def test_experiment_two_compares_all_six_cities(self):
        result = app.experiment_two()
        self.assertEqual(len(result["cities"]), 6)
        delhi = next(city for city in result["cities"] if city["city"] == "Delhi")
        self.assertEqual(delhi["days"], 31)
        self.assertEqual(delhi["hot_days"], 19)
        self.assertEqual(delhi["average"], 40.37)

    def test_experiment_three_normalizes_and_filters_locations(self):
        result = app.experiment_three({"q": [""], "mode": ["all"], "page": ["1"]})
        self.assertEqual(result["metadata"]["location_count"], 543)
        self.assertEqual(result["metadata"]["longest_location"], "Thiruvananthapuram")
        starts_ban = app.experiment_three({"q": [""], "mode": ["starts-ban"], "page": ["1"]})
        self.assertGreater(starts_ban["total_matches"], 0)

    def test_experiment_four_runs_each_polymorphic_analyzer(self):
        for analyzer in ("temperature", "rainfall", "air-quality", "humidity", "regions"):
            with self.subTest(analyzer=analyzer):
                result = app.experiment_four({"analyzer": [analyzer]})
                self.assertGreater(result["rows_loaded"], 0)
                self.assertTrue(result["series"])
                self.assertTrue(result["summary"])

    def test_experiment_five_runs_concurrent_sensor_checks(self):
        result = app.experiment_five({"station": ["Wanaparthy"], "days": ["15"]})
        self.assertEqual(result["sensors"]["temperature"]["valid"], 15)
        self.assertEqual(result["sensors"]["wind_speed"]["errors"], [
            {"date": "01-May-22", "message": "wind speed reading missing"},
            {"date": "06-May-22", "message": "wind speed reading missing"},
            {"date": "08-May-22", "message": "wind speed reading missing"},
            {"date": "09-May-22", "message": "wind speed reading missing"},
            {"date": "10-May-22", "message": "wind speed reading missing"},
            {"date": "13-May-22", "message": "wind speed reading missing"},
            {"date": "14-May-22", "message": "wind speed reading missing"},
        ])
        self.assertEqual(result["faulty_reading"]["temperature"], 87.0)

    def test_experiment_six_summarizes_selected_stations(self):
        result = app.experiment_six({"station": ["Adilabad Rural,Wanaparthy"]})
        summaries = {item["station"]: item for item in result["stations"]}
        self.assertEqual(summaries["Adilabad Rural"]["days_observed"], 31)
        self.assertEqual(summaries["Wanaparthy"]["days_observed"], 12)


if __name__ == "__main__":
    unittest.main()
