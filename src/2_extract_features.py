from pymatgen import Structure
from matminer.featurizers.composition import ElementProperty
import pandas as pd
import os

def extract_features():
    # Load configuration
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Initialize featurizer
    ep = ElementProperty.from_preset("magpie")
    
    # Process all CIF files
    features = []
    structure_dir = config["materials_project"]["structure_dir"]
    for cif_file in os.listdir(structure_dir):
        if cif_file.endswith(".cif"):
            struct = Structure.from_file(os.path.join(structure_dir, cif_file))
            formula = struct.composition.reduced_formula
            feats = ep.featurize(struct.composition)
            features.append([formula] + feats)
    
    # Save features
    df = pd.DataFrame(features, columns=["formula"] + ep.feature_labels())
    df.to_csv(os.path.join(config["paths"]["features_dir"], "features.csv"), index=False)

if __name__ == "__main__":
    extract_features()