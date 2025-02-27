# scripts/utils/structure_utils.py
import logging
from pymatgen.core import Structure, Lattice
from mp_api.client import MPRester
import re

def get_mp_structure(formula, api_key):
    """
    Intenta obtener la estructura desde Materials Project.
    Devuelve None si no la encuentra o si hay error.
    """
    try:
        mpr = MPRester(api_key)
        # Buscar por formula
        results = mpr.materials.search(formula=formula, fields=["material_id"])
        if not results:
            logging.warning(f"No se encontró {formula} en Materials Project.")
            return None

        material_id = results[0].material_id
        # Obtener la estructura
        structure = mpr.get_structure_by_material_id(material_id, conventional_unit_cell=False)
        logging.info(f"Descargada estructura de {formula}, MP-ID: {material_id}")
        return structure

    except Exception as e:
        logging.warning(f"Fallo al obtener estructura MP para {formula}: {e}")
        return None

def predict_structure_by_substitution(formula):
    """
    Placeholder de predicción por sustitución química.
    """
    logging.info(f"Predicción por sustitución no implementada. (formula: {formula})")
    return None

def generate_prototypical_structure(formula, prototype="ABX2"):
    """
    Genera estructuras prototípicas ABX2 o AB3
    """
    elements = re.findall(r'([A-Z][a-z]?)', formula)
    if not elements:
        logging.warning(f"No se pudieron parsear elementos en la fórmula: {formula}")
        return None

    A = elements[0] if len(elements) > 0 else "A"
    B = elements[1] if len(elements) > 1 else "B"

    if prototype == "ABX2":
        # Ejemplo: Celda hexagonal P-3m1
        a = 3.0
        c = 5.0
        lattice = Lattice.hexagonal(a=a, c=c)
        coords = [
            [0.0, 0.0, 0.0],    # A
            [1/3, 2/3, 0.5],    # B
            [2/3, 1/3, 0.25],   # X
            [2/3, 1/3, 0.75],   # X2
        ]
        species = [
            A, B,
            elements[2] if len(elements) > 2 else "X",
            elements[2] if len(elements) > 2 else "X"
        ]
        structure = Structure(lattice, species, coords)
        logging.info(f"Estructura prototípica ABX2 (hexagonal) generada para {formula}")
        return structure

    elif prototype == "AB3":
        # Ejemplo: Celda cúbica Pm-3m
        a = 4.0
        lattice = Lattice.cubic(a)
        coords = [
            [0.0, 0.0, 0.0],   # A
            [0.5, 0.5, 0.0],   # B
            [0.5, 0.0, 0.5],   # B
            [0.0, 0.5, 0.5],   # B
        ]
        species = [A, B, B, B]
        structure = Structure(lattice, species, coords)
        logging.info(f"Estructura prototípica AB3 (cúbica) generada para {formula}")
        return structure

    else:
        logging.warning(f"Prototipo desconocido: {prototype}")
        return None

def generate_fallback_structure(formula):
    """
    Genera una estructura cúbica arbitraria de fallback.
    """
    a = 4.2
    lattice = Lattice.cubic(a)
    coords = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
    ]
    species = ["X", "X"]
    structure = Structure(lattice, species, coords)
    logging.info(f"Estructura cúbica fallback generada para {formula}")
    return structure