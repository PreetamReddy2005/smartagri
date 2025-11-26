#!/usr/bin/env python3
"""
Plant Disease Detection Module
Provides AI-powered leaf disease detection using MobileNetV2
Includes mock mode for testing without a trained model
"""

import os
import random
import numpy as np
from PIL import Image

# Try to import TensorFlow - gracefully degrade if not available
try:
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not available. Running in MOCK MODE only.")

# Configuration
MODEL_PATH = "plant_disease_model.h5"
IMG_SIZE = (224, 224)

# Comprehensive disease classes for common crops
CLASS_NAMES = [
    "Healthy",
    "Early_Blight",
    "Late_Blight",
    "Leaf_Spot",
    "Powdery_Mildew",
    "Bacterial_Wilt",
    "Mosaic_Virus",
    "Rust",
    "Anthracnose",
    "Septoria_Leaf_Spot",
    "Target_Spot"
]

# Disease information and treatment recommendations
DISEASE_INFO = {
    "Healthy": {
        "severity": "None",
        "description": "Plant appears healthy with no visible signs of disease.",
        "treatment": "Continue regular monitoring and maintain good agricultural practices.",
        "prevention": [
            "Maintain proper spacing between plants",
            "Ensure adequate air circulation",
            "Water at base of plants, avoid wetting leaves",
            "Regular inspection for early disease detection"
        ]
    },
    "Early_Blight": {
        "severity": "Medium",
        "description": "Fungal disease causing dark spots with concentric rings on older leaves.",
        "treatment": "Apply copper-based fungicide or chlorothalonil. Remove infected leaves.",
        "prevention": [
            "Crop rotation (3-year cycle)",
            "Mulch to prevent soil splash",
            "Avoid overhead watering",
            "Remove plant debris after harvest"
        ]
    },
    "Late_Blight": {
        "severity": "High",
        "description": "Devastating fungal disease causing water-soaked lesions on leaves and stems.",
        "treatment": "Immediate fungicide application (mancozeb or copper). Remove severely infected plants.",
        "prevention": [
            "Plant resistant varieties",
            "Ensure good air circulation",
            "Avoid overhead irrigation",
            "Monitor weather for favorable conditions (cool, wet)"
        ]
    },
    "Leaf_Spot": {
        "severity": "Medium",
        "description": "Fungal or bacterial spots on leaves, may have yellow halos.",
        "treatment": "Apply appropriate fungicide or bactericide. Improve air circulation.",
        "prevention": [
            "Space plants properly",
            "Water early in day",
            "Remove infected leaves promptly",
            "Use drip irrigation"
        ]
    },
    "Powdery_Mildew": {
        "severity": "Medium",
        "description": "White powdery fungal growth on leaf surfaces.",
        "treatment": "Apply sulfur-based fungicide or neem oil. Increase air circulation.",
        "prevention": [
            "Avoid excessive nitrogen fertilization",
            "Ensure adequate spacing",
            "Remove infected plant parts",
            "Plant in sunny locations"
        ]
    },
    "Bacterial_Wilt": {
        "severity": "High",
        "description": "Bacterial infection causing rapid wilting and plant death.",
        "treatment": "No cure available. Remove and destroy infected plants immediately.",
        "prevention": [
            "Use disease-free seeds/transplants",
            "Control insect vectors (beetles)",
            "Crop rotation",
            "Avoid working with plants when wet"
        ]
    },
    "Mosaic_Virus": {
        "severity": "High",
        "description": "Viral disease causing mottled, discolored leaves and stunted growth.",
        "treatment": "No cure. Remove infected plants to prevent spread.",
        "prevention": [
            "Use virus-resistant varieties",
            "Control aphid populations",
            "Remove weeds that harbor viruses",
            "Sanitize tools between plants"
        ]
    },
    "Rust": {
        "severity": "Medium",
        "description": "Fungal disease with orange-brown pustules on leaf undersides.",
        "treatment": "Apply fungicide containing myclobutanil or sulfur.",
        "prevention": [
            "Plant resistant varieties",
            "Ensure good air circulation",
            "Avoid overhead watering",
            "Remove infected leaves"
        ]
    },
    "Anthracnose": {
        "severity": "Medium",
        "description": "Fungal disease causing dark, sunken lesions on fruits and leaves.",
        "treatment": "Apply copper-based fungicide. Remove infected plant parts.",
        "prevention": [
            "Crop rotation",
            "Avoid overhead irrigation",
            "Mulch to prevent soil splash",
            "Plant in well-drained soil"
        ]
    },
    "Septoria_Leaf_Spot": {
        "severity": "Medium",
        "description": "Fungal disease with small circular spots with dark borders.",
        "treatment": "Apply chlorothalonil or copper fungicide. Remove lower infected leaves.",
        "prevention": [
            "Mulch around plants",
            "Stake plants for better air flow",
            "Water at soil level",
            "Rotate crops annually"
        ]
    },
    "Target_Spot": {
        "severity": "Medium",
        "description": "Fungal disease with concentric ring patterns on leaves.",
        "treatment": "Apply fungicide and improve cultural practices.",
        "prevention": [
            "Maintain plant spacing",
            "Remove plant debris",
            "Avoid leaf wetness",
            "Use resistant varieties"
        ]
    }
}

class DiseaseDetector:
    """Plant disease detection using deep learning."""
    
    def __init__(self):
        self.model = None
        self.mock_mode = True
        
        if TENSORFLOW_AVAILABLE and os.path.exists(MODEL_PATH):
            try:
                print(f"Loading disease detection model from {MODEL_PATH}...")
                self.model = tf.keras.models.load_model(MODEL_PATH)
                self.mock_mode = False
                print("✅ Model loaded successfully")
            except Exception as e:
                print(f"⚠️  Error loading model: {e}")
                print("Falling back to MOCK MODE")
                self.mock_mode = True
        else:
            if not TENSORFLOW_AVAILABLE:
                print("🔬 Running in MOCK MODE - TensorFlow not installed")
            else:
                print(f"🔬 Running in MOCK MODE - Model file '{MODEL_PATH}' not found")
    
    def preprocess_image(self, image_path):
        """
        Preprocess image for MobileNetV2.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed numpy array ready for prediction
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to model input size
            img = img.resize(IMG_SIZE)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            # Preprocess for MobileNetV2
            if TENSORFLOW_AVAILABLE:
                img_array = preprocess_input(img_array)
            else:
                # Normalize manually if TensorFlow not available
                img_array = img_array.astype('float32') / 255.0
            
            return img_array
            
        except Exception as e:
            raise Exception(f"Error preprocessing image: {e}")
    
    def predict_disease(self, image_path):
        """
        Predict disease from a leaf image.
        
        Args:
            image_path: Path to the leaf image
            
        Returns:
            dict: {
                "prediction": str (class name),
                "confidence": float (0-100),
                "all_probabilities": dict (class_name: probability),
                "mock": bool,
                "info": dict (disease details)
            }
        """
        if self.mock_mode:
            return self._mock_predict()
        
        try:
            # Preprocess image
            img_array = self.preprocess_image(image_path)
            
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)
            
            # Get probabilities for each class
            probabilities = predictions[0]
            
            # Find the class with highest probability
            predicted_class_idx = np.argmax(probabilities)
            predicted_class = CLASS_NAMES[predicted_class_idx] if predicted_class_idx < len(CLASS_NAMES) else f"Class_{predicted_class_idx}"
            confidence = float(probabilities[predicted_class_idx]) * 100
            
            # Build probability dict for all classes
            all_probs = {}
            for i, class_name in enumerate(CLASS_NAMES):
                if i < len(probabilities):
                    all_probs[class_name] = float(probabilities[i]) * 100
            
            # Get disease info
            disease_info = DISEASE_INFO.get(predicted_class, {
                "severity": "Unknown",
                "description": "No information available for this disease.",
                "treatment": "Consult an agricultural expert.",
                "prevention": []
            })
            
            return {
                "prediction": predicted_class,
                "confidence": round(confidence, 2),
                "all_probabilities": all_probs,
                "mock": False,
                "info": disease_info
            }
            
        except Exception as e:
            # If real prediction fails, fall back to mock
            print(f"⚠️  Prediction error: {e}. Using mock prediction.")
            return self._mock_predict()
    
    def _mock_predict(self):
        """
        Generate a mock prediction for testing purposes.
        
        Returns:
            dict: Mock prediction result
        """
        # Randomly choose a disease class
        predicted_class = random.choice(CLASS_NAMES)
        
        # Generate random confidence
        confidence = random.uniform(75.0, 99.0)
        
        # Generate mock probabilities
        all_probs = {}
        remaining_prob = 100.0 - confidence
        
        # Distribute remaining probability among other classes
        other_classes = [c for c in CLASS_NAMES if c != predicted_class]
        for c in other_classes:
            prob = remaining_prob / len(other_classes)
            # Add some noise
            noise = random.uniform(-prob/2, prob/2)
            all_probs[c] = max(0, prob + noise)
            
        all_probs[predicted_class] = confidence
        
        # Get disease info
        disease_info = DISEASE_INFO.get(predicted_class, {
            "severity": "Unknown",
            "description": "No information available for this disease.",
            "treatment": "Consult an agricultural expert.",
            "prevention": []
        })
        
        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 2),
            "all_probabilities": all_probs,
            "mock": True,
            "info": disease_info
        }
    
    def get_status(self):
        """
        Get current detector status.
        
        Returns:
            dict: Status information
        """
        return {
            "tensorflow_available": TENSORFLOW_AVAILABLE,
            "model_loaded": self.model is not None,
            "mock_mode": self.mock_mode,
            "model_path": MODEL_PATH,
            "supported_classes": CLASS_NAMES
        }


# Global detector instance
detector = DiseaseDetector()


def predict_disease(image_path):
    """
    Convenience function for making predictions.
    
    Args:
        image_path: Path to the leaf image
        
    Returns:
        dict: Prediction results
    """
    return detector.predict_disease(image_path)


def get_detector_status():
    """
    Get detector status.
    
    Returns:
        dict: Status information
    """
    return detector.get_status()


if __name__ == "__main__":
    # Test the detector
    print("\n" + "="*60)
    print("Plant Disease Detector - Test Mode")
    print("="*60)
    
    status = get_detector_status()
    print(f"\nStatus:")
    print(f"  TensorFlow Available: {status['tensorflow_available']}")
    print(f"  Model Loaded: {status['model_loaded']}")
    print(f"  Mock Mode: {status['mock_mode']}")
    print(f"  Supported Classes: {', '.join(status['supported_classes'])}")
    
    # Test with mock prediction
    print(f"\nTesting mock prediction...")
    result = predict_disease("test.jpg")  # File doesn't need to exist for mock
    print(f"\nPrediction Result:")
    print(f"  Class: {result['prediction']}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Mock: {result['mock']}")
    print(f"  All Probabilities: {result['all_probabilities']}")
