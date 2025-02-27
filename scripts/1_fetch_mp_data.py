# scripts/1_fetch_mp_data.py
import pandas as pd
import numpy as np
import yaml
import logging
import ast
import os
from tqdm import tqdm
from pymatgen.core import Composition, Element
from mp_api.client import MPRester
from dotenv import load_dotenv
from utils.structure_utils import get_mp_structure

load_dotenv()
# Configurar logging
logging.basicConfig(
    filename='logs/project.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Cargar config de API
config = yaml.safe_load(open("config/api_config.yaml", "r"))
mp_config = config["materials_project"]
API_KEY = os.environ.get("API_KEY")
mpr = MPRester(API_KEY)

batch_size = mp_config.get("batch_size", 5)  # Default 5
request_delay = mp_config.get("request_delay", 10)  # Default 10
logging.info(f"batch_size={batch_size}, request_delay={request_delay}")

# Propiedades elementales de interés
ELEMENT_PROPS = {
    'atomic_radius': 'atomic_radius_calculated',
    'en_pauling': 'X',
    'ionization_energy': 'ionization_energy',
    'molar_volume': 'molar_volume',
    'valence': 'valence'
}

# Funciones auxiliares
def safe_parse_valence(valence_str):
    """Convierte valencia de texto a un valor numérico."""
    try:
        parsed = ast.literal_eval(valence_str)  # e.g., "(0, 2)" -> (0, 2)
        return parsed[0] if isinstance(parsed, tuple) else parsed
    except:
        return np.nan

def get_element_properties(element: str) -> dict:
    """Obtiene propiedades elementales con manejo de errores."""
    try:
        el = Element(element)
        return {prop: getattr(el, attr, None) for prop, attr in ELEMENT_PROPS.items()}
    except Exception as e:
        logging.warning(f"Error obteniendo propiedades para {element}: {e}")
        return {prop: None for prop in ELEMENT_PROPS}

def fetch_mp_properties(formula: str) -> dict:
    """Obtiene propiedades de Materials Project o genera datos estimados."""
    result_dict = {}
    result_dict["formula"] = formula  # Para no perder la referencia

    try:
        comp = Composition(formula)
        elements = [str(e) for e in comp.elements]

        # 1) Obtener datos de Materials Project
        results = mpr.materials.summary.search(
            formula=formula,
            fields=["material_id", "volume", "band_gap"],
            num_chunks=1
        )
        if results:
            result_dict.update({
                'mp_id': results[0].material_id,
                'volume': results[0].volume,
                'bandgap': results[0].band_gap
            })
        else:
            logging.warning(f"No encontrado en Materials Project (propiedades): {formula}")

        # 2) Intentar descargar la estructura y guardarla
        structure = get_mp_structure(formula, API_KEY)
        if structure:
            cif_dir = "data/processed/structures"
            os.makedirs(cif_dir, exist_ok=True)
            cif_path = os.path.join(cif_dir, f"{formula}.cif")
            structure.to(fmt="cif", filename=cif_path)
            result_dict['cif_path'] = cif_path
        else:
            result_dict['cif_path'] = None

    except Exception as e:
        logging.warning(f"API falló para {formula}: {e}")

    # 3) Obtener propiedades elementales
    try:
        site_labels = ['A', 'B', 'X']  # Asumiendo compuestos tipo ABX2
        for i, elem in enumerate(elements[:3]):
            props = get_element_properties(elem)

            # Cálculo de molar_volume si no está y se tiene atomic_radius
            if not props['molar_volume'] and props['atomic_radius']:
                props['molar_volume'] = (4/3 * np.pi * (props['atomic_radius'] ** 3))

            for prop in ELEMENT_PROPS:
                result_dict[f'{prop}_{site_labels[i]}'] = props[prop]

    except Exception as e:
        logging.error(f"Fallo en cálculo de propiedades elementales para {formula}: {e}")

    return result_dict

def main():
    # Cargar datos de entrada
    df = pd.read_csv("data/raw/chalcopyrites.csv")

    # Descargar/obtener datos de MP y propiedades elementales
    tqdm.pandas()
    df_features = df["Formula"].progress_apply(fetch_mp_properties)
    df_features = pd.DataFrame(df_features.tolist())

    # Unir los datos con el DataFrame original
    df = pd.merge(df, df_features, left_on="Formula", right_on="formula", how="left")

    # Limpieza y validaciones mínimas
    # Convertir valencias a numérico
    for col in ['valence_A', 'valence_B', 'valence_X']:
        if col in df.columns:
            df[col] = df[col].apply(safe_parse_valence)

    # Llenar valencias faltantes con la moda (o cero)
    for col in ['valence_A', 'valence_B', 'valence_X']:
        if col in df.columns:
            if df[col].mode().empty:
                df[col].fillna(0, inplace=True)
            else:
                df[col].fillna(df[col].mode().values[0], inplace=True)

    # Rellenar mp_id faltante
    df['mp_id'] = df['mp_id'].fillna("Unknown")

    # Rellenar volumen y bandgap con la media si faltan
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(df['volume'].mean())
    if 'bandgap' in df.columns:
        df['bandgap'] = df['bandgap'].fillna(df['bandgap'].mean())

    # Rellenar propiedades elementales críticas con la media
    for col in ['atomic_radius_X', 'molar_volume_X', 'ionization_energy_X']:
        if col in df.columns:
            df[col].fillna(df[col].mean(), inplace=True)

    # Eliminar filas con demasiados NaN en columnas esenciales
    essential_columns = [
        'atomic_radius_A', 'atomic_radius_B', 'atomic_radius_X', 
        'molar_volume_A', 'molar_volume_B', 'molar_volume_X',
        'ionization_energy_A', 'ionization_energy_B', 'ionization_energy_X'
    ]
    columns_present = [c for c in essential_columns if c in df.columns]
    rows_before = df.shape[0]
    df.dropna(subset=columns_present, inplace=True)
    rows_after = df.shape[0]
    logging.info(f"Filas eliminadas tras limpieza: {rows_before - rows_after}")

    # Guardar dataset final
    output_path = "data/processed/enhanced_dataset.csv"
    df.to_csv(output_path, index=False)
    logging.info(f"Procesamiento completado. Archivo guardado en {output_path}")

if __name__ == "__main__":
    main()