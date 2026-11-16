"""Streamlit UI smoke test: catches runtime errors that compileall misses."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


class StreamlitSmokeTests(unittest.TestCase):
    def test_initial_screen_renders_without_uncaught_exceptions(self):
        app = AppTest.from_file(APP_PATH, default_timeout=45).run()
        self.assertEqual(
            len(app.exception),
            0,
            "\n".join(str(e.message) for e in app.exception),
        )
        self.assertTrue(any("فاحص" in item.value for item in app.title))

    def test_urgent_report_priority_without_photo(self):
        # Streamlit testing bypasses browser camera/photo capture.
        # Urgent symptom handling must still be available without a photo.
        app = AppTest.from_file(APP_PATH, default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.multiselect), 1)
        app.multiselect[0].set_value(["sudden_loss"]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.error), 1, "Urgent symptoms must display an alert")
        # The engine handles the content; the UI test only checks the alert renders.


if __name__ == "__main__":
    unittest.main()
