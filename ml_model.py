import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import random
import json
from typing import List, Dict, Optional, Tuple
from suggestions import crop_suggestions
from datetime import datetime

class MoisturePredictor:
    def __init__(self):
        # Multiple AI models for ensemble predictions
        self.models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.active_model = 'random_forest'  # Default to best performing model
        self.is_trained = False
        self.data = []  # Store historical data
        self.water_consumption_model = None
        self.crop_models = {}
        self.current_crop = "tomatoes"
        self.model_performance = {}  # Store performance metrics
        self.prediction_history = []  # Store predictions for AI insights

    def simulate_historical_data(self, num_samples=1000):
        """Simulate historical sensor data for training."""
        data = []
        for i in range(num_samples):
            # Simulate realistic sensor readings
            moisture = random.uniform(10, 80)  # 10-80%
            temp = random.uniform(15, 35)  # 15-35°C
            ph = random.uniform(5.0, 9.0)  # 5.0-9.0
            rain = random.choice([True, False])
            water_level = random.uniform(20, 100)  # 20-100%

            # Simulate next moisture based on current conditions
            # Moisture tends to decrease over time, affected by temp, rain, etc.
            moisture_change = -random.uniform(0.5, 2.0)  # Decrease
            if rain:
                moisture_change += random.uniform(5, 15)  # Rain increases moisture
            if temp > 25:
                moisture_change -= random.uniform(0.5, 1.5)  # High temp decreases faster

            next_moisture = max(0, min(100, moisture + moisture_change))

            data.append({
                'moisture': moisture,
                'temp': temp,
                'ph': ph,
                'rain': int(rain),
                'water_level': water_level,
                'next_moisture': next_moisture
            })

        self.data = data
        return data

    def train_model(self):
        """Train all AI models for moisture prediction with performance comparison."""
        if not self.data:
            self.simulate_historical_data()

        df = pd.DataFrame(self.data)
        X = df[['moisture', 'temp', 'ph', 'rain', 'water_level']]
        y = df['next_moisture']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train all models and compare performance
        print("\n🤖 Training AI Models...")
        for model_name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate comprehensive metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation for robust evaluation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
            cv_mse = -cv_scores.mean()
            
            self.model_performance[model_name] = {
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'cv_mse': cv_mse,
                'accuracy': max(0, min(100, (1 - mae/100) * 100))  # Percentage accuracy
            }
            
            print(f"  ✓ {model_name.replace('_', ' ').title()}: MSE={mse:.2f}, MAE={mae:.2f}, R²={r2:.3f}, Acc={self.model_performance[model_name]['accuracy']:.1f}%")
        
        # Select best model based on R² score
        best_model = max(self.model_performance.items(), key=lambda x: x[1]['r2'])[0]
        self.active_model = best_model
        print(f"\n✨ Best AI Model: {best_model.replace('_', ' ').title()}")
        
        self.is_trained = True
        self.water_consumption_model = {'flow_rate': 10}  # liters per second

    def predict_next_moisture(self, current_data: Dict, use_ensemble: bool = True) -> Optional[float]:
        """Predict moisture level using AI models with optional ensemble method."""
        if not self.is_trained:
            return None

        try:
            features = pd.DataFrame([{
                'moisture': current_data.get('moisture', 0),
                'temp': current_data.get('temperature', 25),
                'ph': current_data.get('ph', 7.0),
                'rain': int(current_data.get('rain', False)),
                'water_level': current_data.get('water_level', 50)
            }])

            if use_ensemble:
                # Ensemble prediction: weighted average of all models
                predictions = []
                weights = []
                for model_name, model in self.models.items():
                    pred = model.predict(features)[0]
                    predictions.append(pred)
                    # Weight by R² score (better models have more influence)
                    weights.append(self.model_performance[model_name]['r2'])
                
                # Weighted average
                prediction = np.average(predictions, weights=weights)
            else:
                # Use active model only
                prediction = self.models[self.active_model].predict(features)[0]
            
            prediction = max(0, min(100, prediction))
            
            # Store prediction for AI insights
            self.prediction_history.append({
                'timestamp': datetime.now().isoformat(),
                'prediction': prediction,
                'actual': current_data.get('moisture', 0)
            })
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
            
            return prediction
        except Exception as e:
            print(f"AI Prediction error: {e}")
            return None

    def predict_multi_step(self, current_data: Dict, steps: int = 4) -> List[float]:
        """Predict moisture levels for next few hours (multi-step)."""
        if not self.is_trained:
            return []

        predictions = []
        data = current_data.copy()

        for _ in range(steps):
            next_moisture = self.predict_next_moisture(data)
            if next_moisture is None:
                break
            predictions.append(next_moisture)
            data['moisture'] = next_moisture  # Update for next prediction

        return predictions

    def predict_irrigation_needed(self, current_data: Dict, threshold: Optional[float] = None) -> Dict:
        """Predict if irrigation is needed within next hour."""
        # Use crop-specific threshold if available
        if threshold is None:
            crop_profile = crop_suggestions.get_crop_profile(self.current_crop)
            if crop_profile:
                threshold = crop_profile["moisture_optimal"]["critical"]
            else:
                threshold = 30  # Default fallback

        next_moisture = self.predict_next_moisture(current_data)
        if next_moisture is None:
            return {'needed': False, 'time_until': None, 'predicted_moisture': None}

        needed = next_moisture < threshold
        time_until = 1 if needed else None  # Simplified: assume 1 hour if needed

        return {
            'needed': needed,
            'time_until': time_until,
            'predicted_moisture': next_moisture
        }

    def predict_water_consumption(self, pump_duration: float) -> float:
        """Predict water consumption based on pump duration."""
        if not self.water_consumption_model:
            return 0

        # Adjust consumption based on crop type
        crop_profile = crop_suggestions.get_crop_profile(self.current_crop)
        crop_multiplier = 1.0
        if crop_profile:
            # Different crops have different water requirements
            base_consumption = crop_profile.get("water_amount_per_irrigation", 2.0)
            crop_multiplier = base_consumption / 2.0  # Normalize to default

        return pump_duration * self.water_consumption_model['flow_rate'] * crop_multiplier

    def set_crop_type(self, crop_type: str) -> bool:
        """Set the current crop type for predictions."""
        if crop_type in crop_suggestions.get_available_crops():
            self.current_crop = crop_type
            crop_suggestions.set_crop_type(crop_type)
            return True
        return False

    def get_current_crop(self) -> str:
        """Get the current crop type."""
        return self.current_crop

    def calculate_stress(self, temp: float, moisture: float, humidity: float, pest_pressure: float) -> Dict:
        """
        Calculate crop stress and viability based on environmental factors.
        Returns a dictionary with viability index (0-100) and stress factors.
        """
        # Get optimal ranges for current crop
        profile = crop_suggestions.get_crop_profile(self.current_crop)
        if not profile:
            # Default generic profile
            profile = {
                "temp_optimal": {"min": 20, "max": 30},
                "moisture_optimal": {"min": 40, "max": 80},
                "humidity_optimal": {"min": 50, "max": 70}
            }

        stress_score = 0
        factors = []

        # Temperature Stress
        t_min, t_max = profile["temp_optimal"]["min"], profile["temp_optimal"]["max"]
        if temp < t_min:
            stress = (t_min - temp) * 5  # 5 points per degree deviation
            stress_score += stress
            factors.append(f"Cold Stress (+{stress:.1f})")
        elif temp > t_max:
            stress = (temp - t_max) * 5
            stress_score += stress
            factors.append(f"Heat Stress (+{stress:.1f})")

        # Moisture Stress
        m_min, m_max = profile["moisture_optimal"]["min"], profile["moisture_optimal"]["max"]
        if moisture < m_min:
            stress = (m_min - moisture) * 2  # 2 points per % deviation
            stress_score += stress
            factors.append(f"Drought Stress (+{stress:.1f})")
        elif moisture > m_max:
            stress = (moisture - m_max) * 2
            stress_score += stress
            factors.append(f"Waterlog Stress (+{stress:.1f})")

        # Pest Stress (Direct impact)
        if pest_pressure > 0:
            stress = pest_pressure * 1.5  # High impact
            stress_score += stress
            factors.append(f"Pest Damage (+{stress:.1f})")

        # Calculate Viability (100 - total stress, clamped to 0-100)
        viability = max(0, min(100, 100 - stress_score))

        return {
            "viability": round(viability, 1),
            "stress_score": round(stress_score, 1),
            "factors": factors
        }

    def simulate_step(self, current_state: Dict, overrides: Dict) -> Dict:
        """
        Generate next simulation step based on physics and overrides.
        """
        # Base values from overrides or current state
        temp = overrides.get('temperature', current_state.get('temperature', 25))
        humidity = overrides.get('humidity', current_state.get('humidity', 60))
        moisture = overrides.get('soil_moisture', current_state.get('soil_moisture', 50))
        pest_pressure = overrides.get('pest_pressure', 0)

        # Physics simulation (if not overridden, evolve naturally)
        # For now, we assume overrides are "set points" from the God Mode sliders
        # So we just return them, but we could add drift/noise here if needed.
        
        # Calculate stress based on these new values
        stress_data = self.calculate_stress(temp, moisture, humidity, pest_pressure)

        return {
            "temperature": temp,
            "humidity": humidity,
            "soil_moisture": moisture,
            "pest_pressure": pest_pressure,
            "viability": stress_data["viability"],
            "stress_factors": stress_data["factors"]
        }

    def get_ai_insights(self) -> Dict:
        """Get comprehensive AI insights for dashboard display."""
        insights = {
            'model_performance': self.model_performance,
            'active_model': self.active_model,
            'active_model_name': self.active_model.replace('_', ' ').title(),
            'best_accuracy': max([m['accuracy'] for m in self.model_performance.values()]) if self.model_performance else 0,
            'prediction_count': len(self.prediction_history),
            'current_crop': self.current_crop
        }
        
        # Calculate prediction accuracy if we have history
        if len(self.prediction_history) > 10:
            recent = self.prediction_history[-10:]
            errors = [abs(p['prediction'] - p['actual']) for p in recent]
            insights['recent_accuracy'] = max(0, 100 - np.mean(errors))
            insights['recent_mae'] = np.mean(errors)
        else:
            insights['recent_accuracy'] = None
            insights['recent_mae'] = None
        
        return insights

# Global instance
predictor = MoisturePredictor()
predictor.train_model()  # Train on startup
