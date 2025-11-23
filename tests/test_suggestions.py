import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suggestions import CropSuggestions

class TestCropSuggestions(unittest.TestCase):
    def setUp(self):
        self.suggester = CropSuggestions()

    def test_initialization(self):
        self.assertEqual(self.suggester.current_crop, "tomatoes")
        self.assertIn("tomatoes", self.suggester.crop_profiles)

    def test_get_crop_profile(self):
        profile = self.suggester.get_crop_profile("tomatoes")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "Tomatoes")
        
        # Test default
        profile_default = self.suggester.get_crop_profile()
        self.assertEqual(profile_default["name"], "Tomatoes")
        
        # Test invalid
        profile_invalid = self.suggester.get_crop_profile("invalid")
        self.assertIsNone(profile_invalid)

    def test_analyze_moisture_low(self):
        """Test moisture analysis for low moisture."""
        profile = self.suggester.get_crop_profile("tomatoes")
        # Critical low moisture (below 40)
        current_data = {"moisture": 30}
        ml_predictions = {}
        
        result = self.suggester._analyze_moisture(current_data, ml_predictions, profile)
        
        # Should have critical alert
        self.assertTrue(any(a["type"] == "critical" for a in result["alerts"]))
        self.assertEqual(result["irrigation_advice"]["action"], "immediate_irrigation")

    def test_analyze_moisture_optimal(self):
        """Test moisture analysis for optimal moisture."""
        profile = self.suggester.get_crop_profile("tomatoes")
        # Optimal moisture (60-80)
        current_data = {"moisture": 70}
        ml_predictions = {}
        
        result = self.suggester._analyze_moisture(current_data, ml_predictions, profile)
        
        self.assertEqual(len(result["alerts"]), 0)
        self.assertEqual(len(result["irrigation_advice"]), 0)

    def test_analyze_ph(self):
        """Test pH analysis."""
        profile = self.suggester.get_crop_profile("tomatoes")
        # Low pH
        current_data = {"ph": 4.0}
        result = self.suggester._analyze_ph(current_data, profile)
        self.assertTrue(any(a["type"] == "critical" for a in result["alerts"]))
        self.assertIn("too low", result["alerts"][0]["message"])

    def test_generate_suggestions_structure(self):
        """Test the full suggestion generation structure."""
        current_data = {
            "moisture": 50,
            "temperature": 25,
            "ph": 6.5
        }
        ml_predictions = {"predicted_moisture": 45}
        
        suggestions = self.suggester.generate_suggestions(current_data, ml_predictions)
        
        self.assertIn("alerts", suggestions)
        self.assertIn("recommendations", suggestions)
        self.assertIn("irrigation_advice", suggestions)
        self.assertIn("risk_assessment", suggestions)
        self.assertEqual(suggestions["crop_type"], "tomatoes")

if __name__ == '__main__':
    unittest.main()
