import unittest
import numpy as np
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from damage_detector import DamageDetector

# --- CHANGE THIS LINE ---
class TestDamageDetector(unittest.TestCase):
    
    def setUp(self):
        """Set up a test detector instance before each test."""
        # Ensure the model file exists before running the test
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'anomaly_detection.h5')
        if not os.path.exists(model_path):
            self.skipTest("Model file 'anomaly_detection.h5' not found.")
        
        self.detector = DamageDetector(model_path=model_path)

    def test_model_loaded(self):
        """Test that the AI model is loaded successfully."""
        self.assertIsNotNone(self.detector.model, "Model should be loaded.")

    def test_process_frame_returns_image(self):
        """Test that process_frame returns an image of the same size."""
        # Create a blank black image with the expected input shape
        input_shape = self.detector.model_input_shape
        test_frame = np.zeros((input_shape[0], input_shape[1], 3), dtype=np.uint8)
        
        # Process the frame
        processed_frame = self.detector.process_frame(test_frame)
        
        # Check if the output is an image and has the same dimensions
        self.assertIsInstance(processed_frame, np.ndarray)
        self.assertEqual(processed_frame.shape, test_frame.shape)