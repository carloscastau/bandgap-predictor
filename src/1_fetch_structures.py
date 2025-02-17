import os
import yaml
from dotenv import load_dotenv
from utils import MaterialsProcessor

def env_constructor(loader, node):
    """Custom YAML loader for environment variables"""
    value = loader.construct_scalar(node)
    return os.getenv(value[2:-1])

def fetch_structures():
    # Load configuration
    load_dotenv()
    yaml.add_constructor('!ENV', env_constructor, Loader=yaml.SafeLoader)
    
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Initialize processor
    processor = MaterialsProcessor(config["materials_project"]["api_key"])
    
    # Process formulas
    results = processor.process_formulas(
        config["formulas"],
        batch_size=config["materials_project"]["batch_size"],
        delay=config["materials_project"]["request_delay"]
    )
    
    # Save results
    output_dir = config["materials_project"]["structure_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    for formula, data in results.items():
        if data["structure"]:
            data["structure"].to(
                fmt="cif", 
                filename=os.path.join(output_dir, f"{formula}_{data['source']}.cif")
            )
    
    # Generate report
    success_rate = len(results)/len(config["formulas"])*100
    print(f"\n✅ Success rate: {success_rate:.1f}%")
    print(f"Structures saved to: {output_dir}")

if __name__ == "__main__":
    fetch_structures()