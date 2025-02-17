from pymatgen.core import Composition
from utils import MaterialsProcessor

def generate_molecules():
    # Example: Generate new formulas
    new_formulas = ["BeGaN2", "MgInP2"]
    
    # Fetch/generate structures
    processor = MaterialsProcessor(os.getenv("API_KEY"))
    for formula in new_formulas:
        struct = processor.get_or_create_structure(formula)
        if struct:
            print(f"Generated structure for {formula}")

if __name__ == "__main__":
    generate_molecules()