# 🧪 Materials Structure Fetcher ML database

This project fetches material structures from the **Materials Project API** and generates crystal structures if they are unavailable. The processed structures are saved in **CIF format** for further analysis. For further analysis with ML.

## 📂 Project Structure

├── data/
│ ├── raw/ # Raw data storage 
│ ├── processed/ # Processed data
│ │ ├── features/ # Extracted features
│ │ ├── structures/ # CIF files
│ └── models/ # Trained machine learning models
├── scripts/
│ ├── fetch_structures.py # Main script to fetch structures
│ └── utils.py # Utility functions
├── config.yaml # Configuration file
├── requirements.txt # Python dependencies
├── Dockerfile # Docker container setup
├── .env # API keys and secrets
├── README.md # Project documentation

## 🛠 Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-repo/materials-structure-fetcher.git
   cd materials-structure-fetcher
Set up the environment
Install dependencies:

pip install -r requirements.txt
Set up API key
Create a .env file in the root directory and add:

API_KEY=your_materials_project_api_key
🚀 Usage
Run the script to fetch structures:

python scripts/fetch_structures.py
Example Output:
yaml

✅ Success rate: 85.7%
Structures saved to: data/processed/structures
🐳 Using Docker
Build the Docker image

docker build -t materials-fetcher .
Run the container

docker run --env-file .env materials-fetcher
⚙ Configuration (config.yaml)
Modify config.yaml to adjust settings:
yaml
paths:
  raw_data: "data/raw"
  processed_data: "data/processed"
  features_dir: "data/processed/features"
  model_path: "models/hybrid_model.pkl"

materials_project:
  api_key: !ENV ${API_KEY}  # API key loaded from .env
  batch_size: 5
  request_delay: 10
  structure_dir: "data/processed/structures"

ml:
  test_size: 0.2
  random_state: 42
  n_estimators: 300

formulas:
 - "BeAlN2"
 - ...

🏗 Updating Dockerfile
If you add new dependencies, update the Dockerfile as follows:

Add required packages in requirements.txt
Modify the Dockerfile:
dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scripts/fetch_structures.py"]
Rebuild the image:
docker build -t materials-fetcher .
📜 License
MIT License

📩 Contact
For questions, open an issue or contact ccastanourrego@gmail.com