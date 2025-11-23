import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock paho.mqtt.client before importing visualizer to avoid connection attempts
with patch('paho.mqtt.client.Client'):
    from visualizer import app, socketio

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        """Test the main dashboard route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        # Check if it tries to render the template (we might not have the template file in the test env if isolated, 
        # but here we are in the same dir structure)
        # self.assertIn(b'SmartAgri', response.data) 

    def test_ai_insights_route(self):
        """Test the AI insights API endpoint."""
        # We need to mock the predictor in visualizer
        with patch('visualizer.predictor') as mock_predictor:
            mock_predictor.get_ai_insights.return_value = {
                'accuracy': 95,
                'active_model': 'test_model'
            }
            
            response = self.app.get('/api/ai-insights')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['accuracy'], 95)

    def test_ai_insights_error(self):
        """Test AI insights when predictor is missing."""
        with patch('visualizer.predictor', None):
            response = self.app.get('/api/ai-insights')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
