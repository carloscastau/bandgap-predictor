# scripts/3_generate_structures.py
import os
import logging
import pandas as pd

from utils.structure_utils import (
    predict_structure_by_substitution,
    generate_prototypical_structure,
    generate_fallback_structure
)

logging.basicConfig(
    filename='logs/project.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def main():
    df = pd.read_csv("data/processed/enhanced_dataset.csv")
    cif_dir = "data/processed/structures"
    os.makedirs(cif_dir, exist_ok=True)

    for idx, row in df.iterrows():
        formula = row["Formula"]
        cif_path = row.get("cif_path", None)

        if pd.isna(cif_path) or not cif_path or not os.path.exists(str(cif_path)):
            logging.info(f"No se encontró CIF para {formula}. Se intentará generar...")

            # 1. Predicción por sustitución
            structure = predict_structure_by_substitution(formula)
            if structure:
                out_path = os.path.join(cif_dir, f"{formula}_sub.cif")
                structure.to(fmt="cif", filename=out_path)
                df.loc[idx, "cif_path"] = out_path
                logging.info(f"Estructura por sustitución generada para {formula}")
                continue

            # 2. Generar estructura prototípica
            # Heurística: si la fórmula termina en '2' => ABX2, si no => AB3
            if formula[-1].isdigit():
                last_digit = int(formula[-1])
            else:
                last_digit = 1

            prototype = "ABX2" if last_digit == 2 else "AB3"
            structure = generate_prototypical_structure(formula, prototype=prototype)
            if structure:
                out_path = os.path.join(cif_dir, f"{formula}_proto.cif")
                structure.to(fmt="cif", filename=out_path)
                df.loc[idx, "cif_path"] = out_path
                logging.info(f"Estructura prototípica {prototype} generada para {formula}")
                continue

            # 3. Fallback
            structure = generate_fallback_structure(formula)
            if structure:
                out_path = os.path.join(cif_dir, f"{formula}_fallback.cif")
                structure.to(fmt="cif", filename=out_path)
                df.loc[idx, "cif_path"] = out_path
                logging.info(f"Estructura fallback generada para {formula}")

    df.to_csv("data/processed/enhanced_dataset.csv", index=False)
    logging.info("Estructuras generadas/completadas y dataset actualizado.")

if __name__ == "__main__":
    main()