import unittest

from processing.preprocessing import preprocess_rate, preprocess_weather


class PreprocessWeatherTest(unittest.TestCase):
    def test_cold_needs_warm_clothes(self) -> None:
        result = preprocess_weather({"temp_c": -3.2, "description": "clear sky"})
        self.assertTrue(result["warm_clothes"])

    def test_zero_is_not_cold(self) -> None:
        result = preprocess_weather({"temp_c": 0.0, "description": "fog"})
        self.assertFalse(result["warm_clothes"])

    def test_description_is_kept(self) -> None:
        result = preprocess_weather({"temp_c": 5.0, "description": "fog"})
        self.assertEqual(result["description"], "fog")


class PreprocessRateTest(unittest.TestCase):
    def test_expensive_above_threshold(self) -> None:
        self.assertTrue(preprocess_rate("eur", 100.01)["expensive"])

    def test_threshold_itself_is_not_expensive(self) -> None:
        result = preprocess_rate("usd", 100.0)
        self.assertFalse(result["expensive"])
        self.assertEqual(result["currency"], "USD")

    def test_rate_is_rounded(self) -> None:
        self.assertEqual(preprocess_rate("USD", 92.1549)["rate_to_rub"], 92.15)


if __name__ == "__main__":
    unittest.main()
