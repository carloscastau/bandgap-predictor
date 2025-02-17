import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

def train_model():
    # Load features
    features = pd.read_csv("data/processed/features/features.csv")
    
    # Split data
    X = features.drop(columns=["formula", "bandgap"])  # Features
    y = features["bandgap"]  # Target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    
    # Save model
    joblib.dump(model, "models/hybrid_model.pkl")

if __name__ == "__main__":
    train_model()