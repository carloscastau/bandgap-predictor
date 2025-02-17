import pandas as pd
import numpy as np
from mendeleev import element, get_all_elements
from pubchempy import get_compounds, Compound

# Get all valid element symbols
all_elements = [e.symbol for e in get_all_elements()]
element_symbols = set(all_elements)

# ==================================================================
# SMILES PARSING & ELEMENT PROPERTIES
# ==================================================================
def parse_smiles(smiles):
    """Parse SMILES to extract element symbols and their counts"""
    elements = []
    i = 0
    n = len(smiles)
    
    while i < n:
        if smiles[i] == '[':
            j = i + 1
            while j < n and smiles[j] != ']': j += 1
            if j < n:
                symbol = smiles[i+1:j]
                if symbol in element_symbols: elements.append(symbol)
                i = j + 1
            else: i += 1
        else:
            matched = False
            if i+1 < n:
                two_char = smiles[i] + smiles[i+1].lower()
                if two_char in element_symbols:
                    elements.append(two_char)
                    i += 2
                    matched = True
            if not matched:
                one_char = smiles[i].upper()
                if one_char in element_symbols: elements.append(one_char)
                i += 1
    return elements

def get_valence_electrons(ec):
    """Calculate valence electrons from electron configuration"""
    if not ec:
        return None
    ec_str = str(ec)  # Convert ElectronicConfiguration object to string
    valence_e = 0
    max_n = 0
    for part in ec_str.split():
        if '[' in part:
            continue
        n_str = ''.join([c for c in part if c.isdigit()])
        if not n_str:
            continue
        n = int(n_str[0])
        electrons = int(''.join([c for c in part[len(n_str):] if c.isdigit()]))
        
        if n > max_n:
            max_n = n
            valence_e = electrons
        elif n == max_n:
            valence_e += electrons
    return valence_e

def get_element_data(symbol):
    """Robust atomic property extraction using mendeleev"""
    try:
        el = element(symbol)
        
        data = {
            'element': symbol,  # Include element symbol
            'atomic_number': el.atomic_number,
            'group': el.group_id,
            'period': el.period,
            'block': el.block,
            'valence_electrons': get_valence_electrons(el.ec),
            'ionization_energy': el.ionenergies.get(1),  # First ionization energy in kJ/mol
            'atomic_weight': el.atomic_weight,
            'atomic_radius': el.atomic_radius,
            'covalent_radius': el.covalent_radius,
            'electron_affinity': el.electron_affinity,
            'electronegativity': el.en_pauling,
        }
        
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# ==================================================================
# DERIVED PROPERTIES CALCULATION
# ==================================================================
def calculate_compound_properties(elements):
    """Calculate compound-level properties from element data"""
    element_data = [get_element_data(e) for e in elements]
    
    # Filter out None values
    valid_data = [ed for ed in element_data if ed is not None]
    
    if not valid_data: return {}
    
    # Basic statistics
    electronegativities = [ed['electronegativity'] for ed in valid_data if ed['electronegativity']]
    atomic_masses = [ed['atomic_weight'] for ed in valid_data if ed['atomic_weight']]
    valence_electrons = [ed['valence_electrons'] for ed in valid_data if ed['valence_electrons']]
    
    # Electronegativity difference (max pairwise difference)
    en_diff = max(electronegativities) - min(electronegativities) if len(electronegativities) >=2 else 0
    
    # Ionic character (Pauling's formula)
    ionic_character = 1 - np.exp(-0.25 * (en_diff)**2) if en_diff else 0
    
    return {
        'electronegativity_diff': en_diff,
        'ionic_character(%)': ionic_character * 100,
        'atomic_mass_ratio': max(atomic_masses)/min(atomic_masses) if atomic_masses else None,
        'valence_electron_ratio': max(valence_electrons)/min(valence_electrons) if valence_electrons else None
    }

# ==================================================================
# MAIN EXECUTION FLOW
# ==================================================================
def process_smiles(smiles):
    elements = parse_smiles(smiles)
    if not elements: return None
    
    # Get individual element properties
    element_props = []
    for symbol in elements:
        props = get_element_data(symbol)
        if props: element_props.append(props)
    
    if not element_props:
        print("No valid element data found.")
        return None
    
    # Create DataFrame for element properties
    df_elements = pd.DataFrame(element_props)
    
    # Ensure all required columns are present
    required_columns = [
        'element', 'atomic_number', 'group', 'period', 'block', 'valence_electrons', 
        'ionization_energy', 'atomic_weight', 'atomic_radius', 
        'covalent_radius', 'electron_affinity', 'electronegativity'
    ]
    
    for col in required_columns:
        if col not in df_elements.columns:
            df_elements[col] = None  # Add missing columns with None values
    
    # Get compound-level properties
    compound_props = calculate_compound_properties(elements)
    
    # Add a row for the molecule with compound-level properties
    molecule_row = {
        'element': 'Molecule',  # Label for the molecule row
        'atomic_number': None,
        'group': None,
        'period': None,
        'block': None,
        'valence_electrons': None,
        'ionization_energy': None,
        'atomic_weight': None,
        'atomic_radius': None,
        'covalent_radius': None,
        'electron_affinity': None,
        'electronegativity': None,
    }
    molecule_row.update(compound_props)  # Add compound-level properties
    
    # Append the molecule row to the DataFrame
    df_molecule = pd.DataFrame([molecule_row])
    df_final = pd.concat([df_elements, df_molecule], ignore_index=True)
    
    # Clean column names
    df_final.columns = [col.replace('_', ' ').title() for col in df_final.columns]
    
    return df_final

# ==================================================================
# USER INTERFACE
# ==================================================================
if __name__ == "__main__":
    smiles = input("Enter SMILES notation (e.g., [Cu]GaS): ").strip()
    result = process_smiles(smiles)
    
    if result is not None:
        print("\nAdvanced Atomic Properties Dataset:")
        print(result.round(2).to_string(index=False))
        result.to_csv('compound_properties.csv', index=False)
        print("\nDataset saved to 'compound_properties.csv'")
    else:
        print("Invalid SMILES or no elements found.")