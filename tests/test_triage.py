import unittest

import numpy as np

from triage import triage
from eye_quality import assess_photo_quality
from triage_export import build_triage_bundle


class TriageTests(unittest.TestCase):
    def test_urgent_symptoms_override_bad_photo(self):
        result = triage(["sudden_loss"], image_quality_ok=False)
        self.assertEqual(result["priority"], "urgent")
        self.assertTrue(result["needs_retake"])
        self.assertIsNone(result["disease_probability"])
        self.assertIsNone(result["medical_diagnosis"])

    def test_chemical_exposure_is_emergency(self):
        result = triage(["chemical"], image_quality_ok=True)
        self.assertEqual(result["priority"], "urgent")
        self.assertIn("غسلها", result["action"])

    def test_diabetes_prompts_appointment_not_eye_diagnosis(self):
        result = triage([], has_diabetes=True, image_quality_ok=True)
        self.assertEqual(result["priority"], "appointment")
        self.assertFalse(result["validated_model"])

    def test_no_symptoms_does_not_claim_healthy_eye(self):
        result = triage([], image_quality_ok=True)
        self.assertEqual(result["priority"], "informational")
        self.assertIn("ليست شهادة", result["action"])

    def test_external_eye_cannot_assess_retina(self):
        result = triage(["blur"], image_type="external")
        self.assertIn("لا تُظهر الشبكية", result["image_note"])

    def test_symptom_code_validation(self):
        with self.assertRaises(ValueError):
            triage(["something_else"])

    def test_fhir_has_no_fake_disease_probability(self):
        result = triage(["blur"], image_quality_ok=True)
        photo = assess_photo_quality(np.full((400, 400, 3), 125, dtype=np.uint8), "external")
        bundle = build_triage_bundle(result, photo, age=42, symptoms=["blur"])
        types = {e["resource"]["resourceType"] for e in bundle["entry"]}
        self.assertEqual(types, {"Patient", "Observation", "QuestionnaireResponse", "Communication"})
        self.assertNotIn("RiskAssessment", types)
        serialized = str(bundle)
        self.assertNotIn("probabilityDecimal", serialized)
        self.assertNotIn("birthDate", serialized)


class ImageQualityTests(unittest.TestCase):
    def test_flat_photo_is_rejected_for_blur(self):
        plain = np.full((512, 512, 3), 130, dtype=np.uint8)
        q = assess_photo_quality(plain, "external")
        self.assertFalse(q["ok"])
        self.assertFalse(q["anatomy_verified"])

    def test_contrast_pattern_meets_experimental_gate(self):
        yy, xx = np.indices((512, 512))
        pattern = np.where((xx // 12 + yy // 12) % 2, 175, 75).astype(np.uint8)
        rgb = np.repeat(pattern[:, :, None], 3, axis=2)
        q = assess_photo_quality(rgb, "external")
        self.assertTrue(q["ok"])
        self.assertFalse(q["anatomy_verified"])

    def test_black_fundus_frame_fails(self):
        blank = np.zeros((512, 512, 3), dtype=np.uint8)
        q = assess_photo_quality(blank, "fundus")
        self.assertFalse(q["ok"])


if __name__ == "__main__":
    unittest.main()
