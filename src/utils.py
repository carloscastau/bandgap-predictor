import os
import time
import logging
from pymatgen.core import Structure, Composition, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.structure_prediction.substitutor import Substitutor
from pymatgen.analysis.prototypes import AflowPrototypeMatcher
from mp_api.client import MPRester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaterialsProcessor:
    def __init__(self, api_key):
        self.mpr = MPRester(api_key)
        self.cached_structures = {}

    def retry(self, func, max_retries=3, delay=2):
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying due to error: {e}. Attempt {attempt + 2}/{max_retries}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise e

    def get_or_create_structure(self, formula):
        """Multi-stage structure acquisition pipeline"""
        try:
            if formula in self.cached_structures:
                logger.info(f"Using cached structure for {formula}")
                return self.cached_structures[formula]
            
            # Stage 1: Check Materials Project
            struct = self._get_mp_structure(formula)
            if struct:
                self.cached_structures[formula] = struct
                return struct

            # Stage 2: Generate structure
            struct = self.generate_ideal_structure(formula)
            if struct:
                self.cached_structures[formula] = struct
                return struct
            
            return None
        except Exception as e:
            logger.error(f"Error processing {formula}: {str(e)}")
            return None

    def _get_mp_structure(self, formula):
        """Get structure from Materials Project"""
        try:
            docs = self.mpr.summary.search(
                formula=formula, 
                fields=["structure", "symmetry"],
                num_chunks=1
            )
            if docs:
                struct = docs[0].structure
                logger.info(f"Found MP structure: {formula}")
                return struct
            return None
        except Exception as e:
            logger.warning(f"MP query failed for {formula}: {str(e)}")
            return None

    def generate_ideal_structure(self, formula):
        """Automated structure generation pipeline"""
        try:
            comp = Composition(formula)
            
            # Attempt 1: Prototype matching
            if struct := self._match_prototype(comp):
                return struct
                
            # Attempt 2: Chemical substitution
            if struct := self._predict_substitution(comp):
                return struct
                
            # Attempt 3: Composition-based heuristic
            return self._generate_fallback(comp)
            
        except Exception as e:
            logger.error(f"Generation failed for {formula}: {str(e)}")
            return None

    def _match_prototype(self, comp):
        """Match to known crystal prototypes"""
        try:
            matcher = AflowPrototypeMatcher()
            prototypes = matcher.get_prototypes(comp)
            if prototypes:
                return prototypes[0]["structure"]
        except Exception as e:
            logger.warning(f"Prototype match failed: {str(e)}")
        return None

    def _predict_substitution(self, comp):
        """Predict structure via chemical substitution"""
        try:
            substitutor = Substitutor(threshold=0.1)
            predictions = substitutor.pred_from_comp(comp)
            if predictions:
                return predictions[0]["structure"]
        except Exception as e:
            logger.warning(f"Substitution failed: {str(e)}")
        return None

    def _generate_fallback(self, comp):
        """Generate structure based on composition heuristics"""
        elements = [e.symbol for e in comp.elements]
        ratios = [comp[e] for e in comp.elements]
        
        # Common structure heuristics
        if len(comp) == 3 and sum(ratios) == 4:  # ABX2 type
            return self._generate_ABX2(comp)
            
        if len(comp) == 2:  # Binary compound
            return Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.0),
                                           elements, [[0,0,0], [0.5,0.5,0.5]])

        # Generic cubic fallback
        return Structure.from_spacegroup("Pm-3m", Lattice.cubic(4.0),
                                       [elements[0]], [[0,0,0]])

    def _generate_ABX2(self, comp):
        """Generate common ABX2 structures"""
        try:
            # Try wurtzite-like structure first
            return Structure.from_spacegroup("P6₃mc",
                Lattice.hexagonal(3.0, 5.0),
                comp.elements,
                [[1/3, 2/3, 0], [0,0,0.5], [1/3, 2/3, 0.375]]
            )
        except:
            # Fallback to tetragonal
            return Structure.from_spacegroup("I-42d",
                Lattice.tetragonal(5.0, 10.0),
                comp.elements,
                [[0,0,0], [0.5,0.5,0.5], [0.25,0.25,0.125]]
            )

    def process_formulas(self, formulas, batch_size=5, delay=10):
        """Batch processing with retry logic"""
        results = {}
        for i in range(0, len(formulas), batch_size):
            batch = formulas[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{len(formulas)//batch_size + 1}")

            for formula in batch:
                try:
                    logger.info(f"Processing formula: {formula}")
                    struct = self.retry(lambda: self.get_or_create_structure(formula))
                    if struct:
                        results[formula] = {
                            "structure": struct,
                            "symmetry": SpacegroupAnalyzer(struct).get_space_group_symbol(),
                            "source": "MP" if "MP" in self.cached_structures else "Generated"
                        }
                except Exception as e:
                    logger.error(f"Failed to process {formula}: {e}")

            time.sleep(delay)

        logger.info(f"Processed {len(results)}/{len(formulas)} formulas successfully")
        return results