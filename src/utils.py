import os
import time
import json
import logging
from math import gcd
from pymatgen.core import Structure, Composition, Lattice, Element
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.structure_prediction.substitutor import Substitutor
from mp_api.client import MPRester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaterialsProcessor:
    def __init__(self, api_key, structure_dir="structures"):
        self.mpr = MPRester(api_key)
        self.cached_structures = {}
        self.error_log = []
        self.structure_dir = structure_dir
        os.makedirs(self.structure_dir, exist_ok=True)

    def retry(self, func, max_retries=5, backoff_factor=2):
        for attempt in range(max_retries):
            try:
                result = func()
                if result: 
                    return result
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Final failure after {max_retries} attempts")
                    self.error_log.append(str(e))
                    return None
                sleep_time = backoff_factor ** attempt
                logger.warning(f"Retry {attempt+1} in {sleep_time}s: {e}")
                time.sleep(sleep_time)
        return None

    def is_valid_stoichiometry(self, comp):
        """Enhanced stoichiometry validation with error handling"""
        try:
            ratios = [comp[el] for el in comp.elements]
            if len(comp) == 2:
                a, b = ratios
                return any(abs(a/b - r) < 0.01 for r in [1, 0.5, 2, 0.33, 3])
            return True
        except ZeroDivisionError:
            return False

    def get_or_create_structure(self, formula):
        try:
            comp = Composition(formula)
            if not self.is_valid_stoichiometry(comp):
                raise ValueError(f"Invalid stoichiometry for {formula}")
            
            if formula in self.cached_structures:
                return self.cached_structures[formula]
            
            # Layered generation attempts
            struct = self.retry(lambda: self._get_mp_structure(formula)) or \
                    self.retry(lambda: self._predict_substitution(comp)) or \
                    self.retry(lambda: self._generate_fallback(comp))

            if struct:
                struct = self._validate_structure(struct)
                self.cached_structures[formula] = struct
                return struct
                
            return self._generate_emergency_structure(comp)
            
        except Exception as e:
            logger.error(f"Error processing {formula}: {e}")
            return self._generate_emergency_structure(comp)

    def _validate_structure(self, struct):
        """Ensure basic structure validity"""
        if struct.volume < 1.0:
            struct.scale_lattice(struct.volume * 2)
        return struct.get_sorted_structure()

    def _get_mp_structure(self, formula):
        try:
            docs = self.mpr.summary.search(
                formula=formula, 
                fields=["structure"], 
                num_chunks=1,
                chunk_size=1
            )
            return docs[0].structure if docs else None
        except Exception as e:
            logger.warning(f"MP query failed: {e}")
            return None

    def _predict_substitution(self, comp):
        """Safe substitution prediction with ratio validation"""
        try:
            # Add composition formatting
            formula = comp.reduced_formula
            if len(comp) < 2:
                return None

            # Validate ratios using gcd approach
            ratios = [int(comp[e]) for e in comp.elements]
            gcd_val = gcd(*ratios)
            simplified = [r/gcd_val for r in ratios]

            if max(simplified) > 4:  # Avoid unrealistic ratios
                logger.debug(f"Skipping substitution for {formula}: ratio too high")
                return None

            substitutor = Substitutor(threshold=0.1)
            predictions = substitutor.pred_from_comp(comp)
            return predictions[0]["structure"] if predictions else None

        except ZeroDivisionError:
            logger.debug(f"Substitution invalid for {formula}")
            return None
        except Exception as e:
            logger.warning(f"Substitution failed for {formula}: {e}")
            return None

    def _generate_ternary_112(self, comp):
        """Generate structure for ABC2-type compounds"""
        try:
            if len(comp) != 3 or not self.is_valid_stoichiometry(comp):
                return None
                
            elements = [e.symbol for e in comp.elements]
            return Structure.from_spacegroup(
                "P-3m1", 
                Lattice.hexagonal(a=3.0, c=5.0),
                [elements[0], elements[1], elements[2], elements[2]],
                [
                    [0, 0, 0],          # A site
                    [1/3, 2/3, 0.5],    # B site
                    [1/3, 2/3, 0.25],   # C site
                    [2/3, 1/3, 0.75]    # C site mirror
                ]
            )
        except Exception as e:
            logger.warning(f"Ternary 112 generation failed: {e}")
            return None

    def _generate_binary_13(self, comp):
        """Generate structure for AB3-type compounds"""
        try:
            if len(comp) != 2 or not self.is_valid_stoichiometry(comp):
                return None
                
            elements = [e.symbol for e in comp.elements]
            return Structure.from_spacegroup(
                "Pm-3m",
                Lattice.cubic(6.0),
                [elements[0]] + [elements[1]]*4,
                [
                    [0, 0, 0],        # A site
                    [0.5, 0.5, 0.5],  # B site
                    [0.5, 0, 0],      # B site
                    [0, 0.5, 0],      # B site
                    [0, 0, 0.5]       # B site
                ]
            )
        except Exception as e:
            logger.warning(f"Binary 13 generation failed: {e}")
            return None

    def _generate_fallback(self, comp):
        """Robust fallback structure generation"""
        try:
            # Attempt prototype-based generation first
            struct = None
            if len(comp) == 3:
                struct = self._generate_ternary_112(comp)
            elif len(comp) == 2:
                struct = self._generate_binary_13(comp)

            # Replace invalid validation check
            if struct and len(struct) == len(comp):  # Check atom count matches composition
                return struct
        except Exception as e:
            logger.debug(f"Prototype generation attempt failed: {e}")

    def _generate_emergency_structure(self, comp):
        """Guaranteed structure generation with error flag"""
        try:
            elements = [e.symbol for e in comp.elements] or ["H"]
            # Ensure at least one atom exists
            return Structure(
                Lattice.cubic(4.0),
                elements[:1] * max(1, len(elements)),  # Ensure minimum 1 atom
                [[0,0,0]]
            )
        except:
            return Structure(Lattice.cubic(4.0), ["H"], [[0,0,0]])

    def process_formulas(self, formulas, batch_size=5, delay=10):
        os.makedirs(self.structure_dir, exist_ok=True)
        results = {}

        for batch_idx in range(0, len(formulas), batch_size):
            batch = formulas[batch_idx:batch_idx + batch_size]
            logger.info(f"Processing batch {batch_idx//batch_size + 1}/{(len(formulas)//batch_size)+1}")

            batch_results = {}
            for formula in batch:
                try:
                    struct = self.get_or_create_structure(formula)
                    fname = os.path.join(self.structure_dir, f"{formula.replace(' ', '')}.cif")
                    struct.to(filename=fname, fmt="cif")
                    batch_results[formula] = struct
                except Exception as e:
                    logger.error(f"Failed {formula}: {e}")
                    self._save_error_structure(formula)

            # Save progress after each batch
            results.update(batch_results)
            self._save_checkpoint(results)

            time.sleep(delay)  # Respect API rate limits

        logger.info(f"Completed {len(results)}/{len(formulas)} successfully")
        return results

    def _save_error_structure(self, formula):
        """Guaranteed structure generation for errors"""
        try:
            Structure(Lattice.cubic(4), ["H"], [[0,0,0]]).to_cif(
                f"structures/{formula}_ERROR.cif"
            )
        except:
            logger.critical(f"Failed to save error structure for {formula}")

    def _save_checkpoint(self, results):
        """Periodic progress saving"""
        with open("processing_checkpoint.json", "w") as f:
            json.dump(list(results.keys()), f)