#!/usr/bin/env python3
"""
Crop-specific suggestions and recommendations for smart agriculture.
Provides intelligent advice based on crop type, current conditions, and ML predictions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

class CropSuggestions:
    def __init__(self):
        # Crop profiles with optimal ranges and characteristics
        self.crop_profiles = {
            "tomatoes": {
                "name": "Tomatoes",
                "moisture_optimal": {"min": 60, "max": 80, "critical": 40},
                "ph_optimal": {"min": 6.0, "max": 6.8, "critical_low": 5.5, "critical_high": 7.5},
                "temp_optimal": {"min": 18, "max": 27, "critical_low": 10, "critical_high": 35},
                "watering_frequency": "daily",
                "water_amount_per_irrigation": 2.5,  # liters per plant
                "growth_stage_sensitivity": {
                    "seedling": {"moisture_multiplier": 1.2, "ph_sensitivity": "high"},
                    "flowering": {"moisture_multiplier": 1.0, "ph_sensitivity": "medium"},
                    "fruiting": {"moisture_multiplier": 0.9, "ph_sensitivity": "low"}
                },
                "common_issues": ["blossom_end_rot", "cracking", "yellow_leaves"],
                "recommendations": [
                    "Ensure consistent moisture to prevent cracking",
                    "Monitor calcium levels for blossom end rot prevention",
                    "Stake plants for better air circulation"
                ]
            },
            "lettuce": {
                "name": "Lettuce",
                "moisture_optimal": {"min": 70, "max": 90, "critical": 50},
                "ph_optimal": {"min": 6.0, "max": 7.0, "critical_low": 5.5, "critical_high": 7.5},
                "temp_optimal": {"min": 15, "max": 20, "critical_low": 5, "critical_high": 25},
                "watering_frequency": "frequent",
                "water_amount_per_irrigation": 1.0,
                "growth_stage_sensitivity": {
                    "seedling": {"moisture_multiplier": 1.3, "ph_sensitivity": "medium"},
                    "growing": {"moisture_multiplier": 1.1, "ph_sensitivity": "low"},
                    "mature": {"moisture_multiplier": 1.0, "ph_sensitivity": "low"}
                },
                "common_issues": ["bolting", "tip_burn", "slug_damage"],
                "recommendations": [
                    "Keep soil consistently moist to prevent bolting",
                    "Provide shade during hot periods",
                    "Harvest outer leaves first for continuous growth"
                ]
            },
            "carrots": {
                "name": "Carrots",
                "moisture_optimal": {"min": 50, "max": 70, "critical": 30},
                "ph_optimal": {"min": 6.0, "max": 6.8, "critical_low": 5.5, "critical_high": 7.5},
                "temp_optimal": {"min": 16, "max": 21, "critical_low": 7, "critical_high": 30},
                "watering_frequency": "moderate",
                "water_amount_per_irrigation": 1.5,
                "growth_stage_sensitivity": {
                    "germination": {"moisture_multiplier": 1.4, "ph_sensitivity": "high"},
                    "root_development": {"moisture_multiplier": 1.0, "ph_sensitivity": "medium"},
                    "maturation": {"moisture_multiplier": 0.8, "ph_sensitivity": "low"}
                },
                "common_issues": ["forking", "cracking", "green_shoulders"],
                "recommendations": [
                    "Ensure deep, consistent watering for straight roots",
                    "Avoid over-fertilization to prevent forking",
                    "Thin seedlings properly for optimal growth"
                ]
            },
            "basil": {
                "name": "Basil",
                "moisture_optimal": {"min": 50, "max": 70, "critical": 35},
                "ph_optimal": {"min": 6.0, "max": 7.0, "critical_low": 5.5, "critical_high": 7.5},
                "temp_optimal": {"min": 21, "max": 27, "critical_low": 13, "critical_high": 32},
                "watering_frequency": "regular",
                "water_amount_per_irrigation": 0.8,
                "growth_stage_sensitivity": {
                    "seedling": {"moisture_multiplier": 1.2, "ph_sensitivity": "medium"},
                    "vegetative": {"moisture_multiplier": 1.0, "ph_sensitivity": "low"},
                    "flowering": {"moisture_multiplier": 0.9, "ph_sensitivity": "low"}
                },
                "common_issues": ["leggy_growth", "downy_mildew", "flower_drop"],
                "recommendations": [
                    "Pinch flowers to maintain leaf production",
                    "Provide good air circulation to prevent mildew",
                    "Harvest regularly to encourage bushy growth"
                ]
            },
            "spinach": {
                "name": "Spinach",
                "moisture_optimal": {"min": 65, "max": 80, "critical": 45},
                "ph_optimal": {"min": 6.5, "max": 7.5, "critical_low": 6.0, "critical_high": 8.0},
                "temp_optimal": {"min": 10, "max": 18, "critical_low": 0, "critical_high": 25},
                "watering_frequency": "regular",
                "water_amount_per_irrigation": 1.2,
                "growth_stage_sensitivity": {
                    "seedling": {"moisture_multiplier": 1.3, "ph_sensitivity": "high"},
                    "growing": {"moisture_multiplier": 1.1, "ph_sensitivity": "medium"},
                    "bolting": {"moisture_multiplier": 0.9, "ph_sensitivity": "low"}
                },
                "common_issues": ["bolting", "leaf_miner", "downy_mildew"],
                "recommendations": [
                    "Harvest young leaves to prevent bolting",
                    "Keep soil cool and moist",
                    "Succession plant for continuous harvest"
                ]
            }
        }

        self.current_crop = "tomatoes"  # Default crop
        self.suggestion_history = []

    def set_crop_type(self, crop_type: str) -> bool:
        """Set the current crop type for suggestions."""
        if crop_type in self.crop_profiles:
            self.current_crop = crop_type
            return True
        return False

    def get_crop_profile(self, crop_type: Optional[str] = None) -> Optional[Dict]:
        """Get the profile for a specific crop or current crop."""
        crop = crop_type or self.current_crop
        return self.crop_profiles.get(crop)

    def get_available_crops(self) -> List[str]:
        """Get list of available crop types."""
        return list(self.crop_profiles.keys())

    def generate_suggestions(self, current_data: Dict, ml_predictions: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive suggestions based on current conditions and ML predictions.

        Args:
            current_data: Current sensor readings (moisture, temp, ph, etc.)
            ml_predictions: ML model predictions

        Returns:
            Dictionary with suggestions, alerts, and recommendations
        """
        crop_profile = self.get_crop_profile()
        if not crop_profile:
            return {"error": "Invalid crop type"}

        suggestions = {
            "crop_type": self.current_crop,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alerts": [],
            "recommendations": [],
            "irrigation_advice": {},
            "maintenance_tips": [],
            "risk_assessment": {}
        }

        # Analyze moisture conditions
        moisture_suggestions = self._analyze_moisture(current_data, ml_predictions, crop_profile)
        suggestions["alerts"].extend(moisture_suggestions["alerts"])
        suggestions["recommendations"].extend(moisture_suggestions["recommendations"])
        suggestions["irrigation_advice"] = moisture_suggestions["irrigation_advice"]

        # Analyze pH conditions
        ph_suggestions = self._analyze_ph(current_data, crop_profile)
        suggestions["alerts"].extend(ph_suggestions["alerts"])
        suggestions["recommendations"].extend(ph_suggestions["recommendations"])

        # Analyze temperature conditions
        temp_suggestions = self._analyze_temperature(current_data, crop_profile)
        suggestions["alerts"].extend(temp_suggestions["alerts"])
        suggestions["recommendations"].extend(temp_suggestions["recommendations"])

        # Generate maintenance tips
        suggestions["maintenance_tips"] = crop_profile.get("recommendations", [])

        # Risk assessment
        suggestions["risk_assessment"] = self._assess_risks(current_data, ml_predictions, crop_profile)

        # Store in history
        self.suggestion_history.append(suggestions)
        if len(self.suggestion_history) > 100:  # Keep last 100 suggestions
            self.suggestion_history.pop(0)

        return suggestions

    def _analyze_moisture(self, current_data: Dict, ml_predictions: Dict, crop_profile: Dict) -> Dict:
        """Analyze moisture conditions and generate suggestions."""
        moisture = current_data.get("moisture")
        if moisture is None:
            return {"alerts": [], "recommendations": [], "irrigation_advice": {}}

        optimal = crop_profile["moisture_optimal"]
        alerts = []
        recommendations = []
        irrigation_advice = {}

        # Check moisture levels
        if moisture < optimal["critical"]:
            alerts.append({
                "type": "critical",
                "sensor": "moisture",
                "message": f"Critical moisture level! {self._get_crop_name()} needs immediate watering.",
                "value": moisture,
                "threshold": optimal["critical"]
            })
            irrigation_advice = {
                "action": "immediate_irrigation",
                "reason": "critical_moisture",
                "suggested_duration": self._calculate_irrigation_duration(moisture, optimal),
                "priority": "high"
            }
        elif moisture < optimal["min"]:
            alerts.append({
                "type": "warning",
                "sensor": "moisture",
                "message": f"Low moisture for {self._get_crop_name()}. Consider watering soon.",
                "value": moisture,
                "threshold": optimal["min"]
            })
            irrigation_advice = {
                "action": "schedule_irrigation",
                "reason": "low_moisture",
                "suggested_duration": self._calculate_irrigation_duration(moisture, optimal),
                "priority": "medium"
            }
        elif moisture > optimal["max"]:
            recommendations.append(f"Soil moisture is high for {self._get_crop_name()}. Reduce watering frequency.")
            irrigation_advice = {
                "action": "reduce_irrigation",
                "reason": "high_moisture",
                "suggested_duration": 0,
                "priority": "low"
            }

        # Check ML predictions
        predicted_moisture = ml_predictions.get("predicted_moisture")
        if predicted_moisture is not None:
            if predicted_moisture < optimal["critical"]:
                alerts.append({
                    "type": "prediction",
                    "sensor": "moisture_forecast",
                    "message": f"ML predicts critical moisture levels soon for {self._get_crop_name()}.",
                    "predicted_value": predicted_moisture,
                    "hours_ahead": 1
                })

        # Multi-step forecast analysis
        forecast = ml_predictions.get("multi_step_forecast", [])
        if forecast:
            critical_hours = []
            for i, pred_moisture in enumerate(forecast):
                if pred_moisture < optimal["critical"]:
                    critical_hours.append(i + 1)

            if critical_hours:
                recommendations.append(f"{self._get_crop_name()} may need watering in {min(critical_hours)} hour(s) based on forecast.")

        return {
            "alerts": alerts,
            "recommendations": recommendations,
            "irrigation_advice": irrigation_advice
        }

    def _analyze_ph(self, current_data: Dict, crop_profile: Dict) -> Dict:
        """Analyze pH conditions and generate suggestions."""
        ph = current_data.get("ph")
        if ph is None:
            return {"alerts": [], "recommendations": []}

        optimal = crop_profile["ph_optimal"]
        alerts = []
        recommendations = []

        if ph < optimal["critical_low"]:
            alerts.append({
                "type": "critical",
                "sensor": "ph",
                "message": f"Soil pH is too low for {self._get_crop_name()}. Add lime to raise pH.",
                "value": ph,
                "threshold": optimal["critical_low"]
            })
        elif ph > optimal["critical_high"]:
            alerts.append({
                "type": "critical",
                "sensor": "ph",
                "message": f"Soil pH is too high for {self._get_crop_name()}. Add sulfur to lower pH.",
                "value": ph,
                "threshold": optimal["critical_high"]
            })
        elif ph < optimal["min"] or ph > optimal["max"]:
            recommendations.append(f"pH level ({ph:.1f}) is outside optimal range for {self._get_crop_name()}. Consider adjustment.")

        return {"alerts": alerts, "recommendations": recommendations}

    def _analyze_temperature(self, current_data: Dict, crop_profile: Dict) -> Dict:
        """Analyze temperature conditions and generate suggestions."""
        temp = current_data.get("temperature")
        if temp is None:
            return {"alerts": [], "recommendations": []}

        optimal = crop_profile["temp_optimal"]
        alerts = []
        recommendations = []

        if temp < optimal["critical_low"]:
            alerts.append({
                "type": "warning",
                "sensor": "temperature",
                "message": f"Temperature too low for {self._get_crop_name()}. Consider frost protection.",
                "value": temp,
                "threshold": optimal["critical_low"]
            })
        elif temp > optimal["critical_high"]:
            alerts.append({
                "type": "warning",
                "sensor": "temperature",
                "message": f"Temperature too high for {self._get_crop_name()}. Provide shade or cooling.",
                "value": temp,
                "threshold": optimal["critical_high"]
            })
        elif temp < optimal["min"] or temp > optimal["max"]:
            recommendations.append(f"Temperature ({temp:.1f} C) is outside optimal range for {self._get_crop_name()}.")

        return {"alerts": alerts, "recommendations": recommendations}

    def _assess_risks(self, current_data: Dict, ml_predictions: Dict, crop_profile: Dict) -> Dict:
        """Assess overall risks based on current conditions."""
        risk_level = "low"
        risk_factors = []

        # Moisture risk
        moisture = current_data.get("moisture")
        if moisture is not None and moisture < crop_profile["moisture_optimal"]["critical"]:
            risk_level = "high"
            risk_factors.append("critical_moisture")

        # pH risk
        ph = current_data.get("ph")
        optimal_ph = crop_profile["ph_optimal"]
        if ph is not None and (ph < optimal_ph["critical_low"] or ph > optimal_ph["critical_high"]):
            risk_level = "high"
            risk_factors.append("extreme_ph")

        # Temperature risk
        temp = current_data.get("temperature")
        optimal_temp = crop_profile["temp_optimal"]
        if temp is not None and (temp < optimal_temp["critical_low"] or temp > optimal_temp["critical_high"]):
            if risk_level == "low":
                risk_level = "medium"
            risk_factors.append("extreme_temperature")

        # ML prediction risk
        irrigation_needed = ml_predictions.get("irrigation_needed", False)
        if irrigation_needed:
            if risk_level == "low":
                risk_level = "medium"
            risk_factors.append("predicted_irrigation_need")

        return {
            "level": risk_level,
            "factors": risk_factors,
            "description": f"Overall risk assessment: {risk_level.upper()}"
        }

    def _calculate_irrigation_duration(self, current_moisture: float, optimal: Dict) -> float:
        """Calculate suggested irrigation duration based on moisture deficit."""
        deficit = optimal["min"] - current_moisture
        if deficit <= 0:
            return 0

        # Base duration calculation (simplified)
        base_duration = 5  # seconds
        duration_multiplier = min(deficit / 20, 3)  # Max 3x multiplier
        return base_duration * duration_multiplier

    def _get_crop_name(self) -> str:
        """Get the display name of the current crop."""
        profile = self.get_crop_profile()
        return profile.get("name", self.current_crop) if profile else self.current_crop

    def get_crop_optimal_ranges(self, crop_type: Optional[str] = None) -> Dict:
        """Get optimal ranges for a crop type."""
        profile = self.get_crop_profile(crop_type)
        if not profile:
            return {}

        return {
            "moisture": profile["moisture_optimal"],
            "ph": profile["ph_optimal"],
            "temperature": profile["temp_optimal"],
            "watering_frequency": profile["watering_frequency"],
            "water_amount_per_irrigation": profile["water_amount_per_irrigation"]
        }

# Global instance
crop_suggestions = CropSuggestions()
