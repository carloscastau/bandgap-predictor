import joblib
import pandas as pd

def predict(formula):
    # Load model
    model = joblib.load("models/hybrid_model.pkl")
    
    # Load features
    features = pd.read_csv("data/processed/features/features.csv")
    
    # Find features for the formula
    sample = features[features["formula"] == formula].drop(columns=["formula", "bandgap"])
    if sample.empty:
        raise ValueError(f"Formula {formula} not found in features")
    
    # Predict bandgap
    return model.predict(sample)[0]

if __name__ == "__main__":
    formula = "BeAlN2"  # Example
    print(f"Predicted bandgap for {formula}: {predict(formula)}")