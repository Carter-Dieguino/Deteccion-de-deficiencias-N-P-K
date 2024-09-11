import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import tkinter as tk
from tkinter import Label, Text, Button
from PIL import Image, ImageTk

# Load pre-trained model (adjust the path to your model)
model = load_model('model_weights.weights.h5')

# Dictionary for deficiencies and recommendations
deficiency_recommendations = {
    0: ("Nitrogen Deficiency", "Apply nitrogen-rich fertilizers like urea."),
    1: ("Phosphorus Deficiency", "Use phosphorus-rich fertilizers like superphosphate."),
    # Add other mappings based on extracted PDF content
}

# Function to preprocess image for prediction
def preprocess_image(img):
    img_array = cv2.resize(img, (224, 224))
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array

# Function to predict disease
def predict_disease(img, model):
    img_array = preprocess_image(img)
    predictions = model.predict(img_array)
    return np.argmax(predictions)

# Function to calculate area using reference object
def calculate_area(leaf_contour, reference_contour, reference_cm2):
    ref_area_pixels = cv2.contourArea(reference_contour)
    leaf_area_pixels = cv2.contourArea(leaf_contour)
    leaf_area_cm2 = (leaf_area_pixels / ref_area_pixels) * reference_cm2
    return leaf_area_cm2

# Initialize GUI
class PlantDiseaseDetectorApp:
    def __init__(self, root, model):
        self.root = root
        self.model = model
        self.video_capture = cv2.VideoCapture(0)
        self.root.title("Plant Disease Detector")
        
        # Video display
        self.video_label = Label(root)
        self.video_label.pack()
        
        # Area display
        self.area_label = Label(root, text="Leaf Area: ")
        self.area_label.pack()
        
        # Disease detection and recommendation display
        self.disease_label = Label(root, text="Detected Disease: ")
        self.disease_label.pack()
        self.recommendation_text = Text(root, height=10, width=50)
        self.recommendation_text.pack()
        
        # Update video feed
        self.update_video()
        
    def update_video(self):
        ret, frame = self.video_capture.read()
        if ret:
            # Split the frame to get leaf and reference areas
            height, width = frame.shape[:2]
            reference_area = frame[:, :width//4]
            leaf_area = frame[:, width//4:]
            
            # Process the leaf area for disease detection
            disease_class = predict_disease(leaf_area, self.model)
            deficiency, recommendation = get_recommendation(disease_class)
            
            # Display disease and recommendation
            self.disease_label.config(text=f"Detected Disease: {deficiency}")
            self.recommendation_text.delete(1.0, tk.END)
            self.recommendation_text.insert(tk.END, recommendation)
            
            # Process the reference area for area calculation
            gray_ref = cv2.cvtColor(reference_area, cv2.COLOR_BGR2GRAY)
            _, thresh_ref = cv2.threshold(gray_ref, 128, 255, cv2.THRESH_BINARY_INV)
            contours_ref, _ = cv2.findContours(thresh_ref, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            gray_leaf = cv2.cvtColor(leaf_area, cv2.COLOR_BGR2GRAY)
            _, thresh_leaf = cv2.threshold(gray_leaf, 128, 255, cv2.THRESH_BINARY_INV)
            contours_leaf, _ = cv2.findContours(thresh_leaf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours_ref and contours_leaf:
                ref_contour = max(contours_ref, key=cv2.contourArea)
                leaf_contour = max(contours_leaf, key=cv2.contourArea)
                leaf_area_cm2 = calculate_area(leaf_contour, ref_contour, 1.0)  # Assuming 1 cm^2 reference
                self.area_label.config(text=f"Leaf Area: {leaf_area_cm2:.2f} cm^2")
            
            # Display video
            combined_frame = np.hstack((reference_area, leaf_area))
            img = Image.fromarray(cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        self.root.after(10, self.update_video)
    
    def __del__(self):
        self.video_capture.release()

# Function to get recommendation based on disease class
def get_recommendation(disease_class):
    deficiency, recommendation = deficiency_recommendations.get(disease_class, ("Unknown", "Consult an expert."))
    return deficiency, recommendation

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = PlantDiseaseDetectorApp(root, model)
    root.mainloop()
