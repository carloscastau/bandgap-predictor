import os
import yaml
from dotenv import load_dotenv
from utils import MaterialsProcessor

def env_constructor(loader, node):
    """Custom YAML loader for environment variables"""
    value = loader.construct_scalar(node)
    return os.getenv(value[2:-1])

def main():
    load_dotenv()
    yaml.add_constructor('!ENV', env_constructor, Loader=yaml.SafeLoader)
    
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    processor = MaterialsProcessor(
    config["materials_project"]["api_key"], 
    config["materials_project"]["structure_dir"]
    )
    results = processor.process_formulas(
        config["formulas"],
        batch_size=config["materials_project"]["batch_size"],
        delay=config["materials_project"]["request_delay"]
    )
    
    print(f"\n✅ Success rate: {len(results)/len(config['formulas'])*100:.1f}%")

if __name__ == "__main__":
    main()