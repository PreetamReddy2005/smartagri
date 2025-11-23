import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model import MoisturePredictor

class TestMoisturePredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = MoisturePredictor()

    def test_initialization(self):
        """Test that the predictor initializes correctly."""
        self.assertFalse(self.predictor.is_trained)
        self.assertEqual(self.predictor.current_crop, "tomatoes")
        self.assertIn('random_forest', self.predictor.models)

    def test_train_model(self):
        """Test model training."""
        # Mock the internal data generation to be faster/deterministic if needed
        # But for now, we'll let it run as it's fast enough
        self.predictor.train_model()
        self.assertTrue(self.predictor.is_trained)
        self.assertIsNotNone(self.predictor.active_model)
        self.assertTrue(len(self.predictor.model_performance) > 0)

    def test_predict_next_moisture_untrained(self):
        """Test prediction before training returns None."""
        prediction = self.predictor.predict_next_moisture({})
        self.assertIsNone(prediction)

    def test_predict_next_moisture_trained(self):
        """Test prediction after training."""
        self.predictor.train_model()
        current_data = {
            'moisture': 50,
            'temperature': 25,
            'ph': 7.0,
            'rain': False,
            'water_level': 80
        }
        prediction = self.predictor.predict_next_moisture(current_data)
        self.assertIsNotNone(prediction)
        self.assertIsInstance(prediction, float)
        self.assertTrue(0 <= prediction <= 100)

    def test_predict_irrigation_needed(self):
        """Test irrigation prediction logic."""
        self.predictor.train_model()
        
        # Case 1: High moisture, no irrigation needed
        current_data_wet = {'moisture': 80, 'temperature': 25, 'ph': 7, 'rain': 0, 'water_level': 80}
        result = self.predictor.predict_irrigation_needed(current_data_wet, threshold=30)
        self.assertFalse(result['needed'])
        
        # Case 2: Very low moisture, irrigation likely needed (depending on model prediction)
        # Since model is probabilistic, we can't strictly assert True without mocking predict_next_moisture
        # So we'll mock predict_next_moisture to return a low value
        with patch.object(self.predictor, 'predict_next_moisture', return_value=20.0):
            result = self.predictor.predict_irrigation_needed(current_data_wet, threshold=30)
            self.assertTrue(result['needed'])
            self.assertEqual(result['time_until'], 1)

    def test_set_crop_type(self):
        """Test changing crop type."""
        success = self.predictor.set_crop_type("lettuce")
        self.assertTrue(success)
        self.assertEqual(self.predictor.current_crop, "lettuce")
        
        fail = self.predictor.set_crop_type("invalid_crop")
        self.assertFalse(fail)
        self.assertEqual(self.predictor.current_crop, "lettuce")  # Should not change

if __name__ == '__main__':
    unittest.main()
