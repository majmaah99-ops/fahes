"""End-to-end route smoke checks for the Vercel FastAPI entrypoint."""
import io
import json
import unittest

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


class VercelFastAPITests(unittest.TestCase):
    def test_homepage_renders_arabic_working_frontend(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("فاحص", response.text)
        self.assertIn('fetch("/api/screen"', response.text)
        self.assertIn('id="camera-start"', response.text)

    def test_health_endpoint_reports_not_diagnostic(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["diagnostic_model"], False)

    def test_no_image_urgent_symptom_still_alerts(self):
        response = client.post(
            "/api/screen",
            data={
                "symptoms": json.dumps(["sudden_loss"]),
                "image_type": "external",
                "has_diabetes": "false",
                "age": "42",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["triage"]["priority"], "urgent")
        self.assertIsNone(data["quality"])
        self.assertIsNone(data["triage"]["disease_probability"])
        obs = next(
            entry["resource"] for entry in data["fhir"]["entry"]
            if entry["resource"]["resourceType"] == "Observation"
        )
        self.assertIn("dataAbsentReason", obs)
        self.assertNotIn("valueBoolean", obs)

    def test_valid_uploaded_image_reports_only_technical_quality(self):
        photo = Image.new("RGB", (400, 400), (125, 125, 125))
        buf = io.BytesIO()
        photo.save(buf, format="PNG")
        response = client.post(
            "/api/screen",
            data={"image_type": "external", "symptoms": "[]", "age": ""},
            files={"file": ("eye.png", buf.getvalue(), "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIsNotNone(data["quality"])
        self.assertFalse(data["quality"]["anatomy_verified"])
        self.assertIsNone(data["triage"]["medical_diagnosis"])

    def test_invalid_image_type_rejected(self):
        response = client.post("/api/screen", data={"image_type": "unrecognized"})
        self.assertEqual(response.status_code, 422)

    def test_non_image_file_rejected(self):
        response = client.post(
            "/api/screen",
            data={"image_type": "external"},
            files={"file": ("not-eye.txt", b"not a real image", "text/plain")},
        )
        self.assertEqual(response.status_code, 422)

    def test_bad_symptom_code_rejected(self):
        response = client.post(
            "/api/screen", data={"symptoms": '["not_a_valid_code"]'}
        )
        self.assertEqual(response.status_code, 422)

    def test_oversized_file_rejected_before_decode(self):
        response = client.post(
            "/api/screen",
            files={"file": ("eye.png", b"Z" * (4 * 1024 * 1024 + 1), "image/png")},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
