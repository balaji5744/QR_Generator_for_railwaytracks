import cv2
import numpy as np
import random
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from database_manager import RailwayDatabaseManager

class DamageDetector:
    def __init__(self, model_path='models/anomaly_detection.h5'):
        try:
            self.model = load_model(model_path)
            self.model_input_shape = self.model.input_shape[1:3]
            self.db_manager = RailwayDatabaseManager()
            # A list of specific components for our simulation
            self.component_types = [
                'BOLT', 'CLIP', 'PLATE', 'SLEEPER', 'ANCHOR', 'SPIKE', 'WASHER'
            ]
            print(f"✅ Successfully loaded real AI model from {model_path}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None

    def process_frame(self, frame):
        if self.model is None:
            cv2.putText(frame, "Error: Model not loaded", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame

        try:
            # --- Image Pre-processing ---
            image = cv2.resize(frame, self.model_input_shape)
            image = image.astype("float") / 255.0
            image = img_to_array(image)
            image = np.expand_dims(image, axis=0)

            # --- AI Model Prediction ---
            crack_probability = self.model.predict(image)[0][0]

            # --- Display Results on Frame ---
            if crack_probability > 0.5:
                label = "Anomaly Detected"
                color = (0, 0, 255) # Red for the general status
                probability = crack_probability * 100
                
                # --- SIMULATE SPECIFIC PART DETECTION ---
                # This runs only when a general anomaly is found
                if probability > 85:
                    self.db_manager.log_anomaly(confidence=float(probability))
                    
                    # Pick a random component to blame for the anomaly
                    damaged_part = random.choice(self.component_types)
                    
                    # Draw a smaller, more specific box in a random location
                    h, w, _ = frame.shape
                    x1 = random.randint(int(w*0.2), int(w*0.8) - 100)
                    y1 = random.randint(int(h*0.5), int(h*0.9) - 100)
                    x2, y2 = x1 + 100, y1 + 50
                    
                    # Draw the specific (simulated) detection with a yellow box and text
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2) 
                    cv2.putText(frame, f"DAMAGED {damaged_part}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            else:
                label = "Normal"
                color = (0, 255, 0) # Green for the general status
                probability = (1 - crack_probability) * 100

            display_label = f"{label}: {probability:.2f}%"
            # Display the general status on the top-left
            cv2.putText(frame, display_label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        except Exception as e:
            print(f"Error during frame processing: {e}")
            return frame

        return frame