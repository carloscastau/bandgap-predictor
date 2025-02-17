FROM mambaorg/micromamba:1.5.1

RUN micromamba install -n base -y -c conda-forge \
    python=3.10 \
    rdkit=2023.09.5 \
    numpy=1.24.3 \
    pandas=2.0.1 \
    scikit-learn=1.3.2 \
    xgboost=1.7.3 \
    mendeleev=0.12.1 \
    joblib=1.3.2 \
    pytorch=2.0.1 \
    cudatoolkit=11.8 -c pytorch -c nvidia

RUN micromamba run -n base pip install transformers==4.28.1 pyyaml==6.0

COPY . /app
WORKDIR /app