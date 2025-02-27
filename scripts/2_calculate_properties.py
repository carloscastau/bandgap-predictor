# scripts/2_calculate_properties.py
import pandas as pd
import numpy as np
import logging
from pymatgen.core import Composition
from utils.thermal_conductivity import slack_thermal_conductivity

logging.basicConfig(
    filename='logs/project.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def calculate_slack_tc(formula, row):
    """
    Estima la conductividad térmica con la ecuación de Slack.
    Toma como referencia el elemento 'X' (ejemplo simplificado).
    """
    from pymatgen.core import Element
    comp = Composition(formula)
    elements = comp.elements
    if not elements:
        return np.nan

    # Tomamos arbitrariamente el último elemento como "X"
    x_el = str(elements[-1])
    try:
        el_obj = Element(x_el)
        return slack_thermal_conductivity(el_obj)
    except:
        return np.nan

def main():
    df = pd.read_csv("data/processed/enhanced_dataset.csv")

    # Ejemplo: crear características adicionales
    if all(col in df.columns for col in ["molar_volume_B", "molar_volume_A"]):
        df['MV_ratio'] = df['molar_volume_B'] / df['molar_volume_A']
    else:
        df['MV_ratio'] = np.nan

    if all(col in df.columns for col in ["en_pauling_B", "en_pauling_A"]):
        df['EN_diff'] = df['en_pauling_B'] - df['en_pauling_A']
    else:
        df['EN_diff'] = np.nan

    # Calcular conductividad térmica "TC_X"
    df['TC_X'] = df.apply(
        lambda row: calculate_slack_tc(row['Formula'], row), axis=1
    )

    # Ajustar la columna que usarás como BandGap de referencia
    # en caso de que tu CSV original la llame "Bandgap" en lugar de "HSE06_bandgap"
    if 'Bandgap' in df.columns:
        df['HSE06_bandgap'] = df['Bandgap']
    else:
        df['HSE06_bandgap'] = np.nan

    # Guardar dataset final
    df.to_csv("data/processed/enhanced_dataset.csv", index=False)
    logging.info("Archivo con propiedades adicionales guardado en data/processed/enhanced_dataset.csv")

if __name__ == "__main__":
    main()