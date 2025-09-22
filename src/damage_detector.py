import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

class DamageDetector:
    def __init__(self, model_path='models/anomaly_detection.h5'):
        """
        Loads the trained Keras model for railway anomaly detection.
        """
        try:
            self.model = load_model(model_path)
            self.model_input_shape = self.model.input_shape[1:3]
            print(f"✅ Successfully loaded real AI model from {model_path}")
            print(f"ℹ️ Model expects input shape: {self.model_input_shape}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None

    def process_frame(self, frame):
        """
        Processes a single video frame to detect anomalies using the loaded model.
        """
        if self.model is None:
            cv2.putText(frame, "Error: Model not loaded", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame

        try:
            image = cv2.resize(frame, self.model_input_shape)
            image = image.astype("float") / 255.0
            image = img_to_array(image)
            image = np.expand_dims(image, axis=0)

            # --- AI Model Prediction (THE FIX IS HERE) ---
            # The model returns the probability of "crack" as a single value.
            crack_probability = self.model.predict(image)[0][0]
            
            # --- Display Results on Frame ---
            # We determine the label based on a 50% threshold.
            if crack_probability > 0.5:
                label = "Anomaly Detected"
                color = (0, 0, 255) # Red
                probability = crack_probability * 100
            else:
                label = "Normal"
                color = (0, 255, 0) # Green
                probability = (1 - crack_probability) * 100

            display_label = f"{label}: {probability:.2f}%"

            cv2.putText(frame, display_label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            if label == "Anomaly Detected" and probability > 85:
                cv2.rectangle(frame, (5, 5), (frame.shape[1] - 5, frame.shape[0] - 5), color, 5)

        except Exception as e:
            print(f"Error during frame processing: {e}")
            return frame

        return frame