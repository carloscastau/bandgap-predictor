# scripts/4_run_regression.py
import pandas as pd
import numpy as np
from pysr import PySRRegressor
import logging
from sklearn.metrics import mean_squared_error, mean_absolute_error

logging.basicConfig(
    filename='logs/project.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def main():
    # 1. Cargar dataset mejorado
    df = pd.read_csv("data/processed/enhanced_dataset.csv")
    
    # 2. Definir columnas de características
    feature_columns = [
        'atomic_radius_A', 'molar_volume_A', 'ionization_energy_A',
        'atomic_radius_B', 'molar_volume_B', 'ionization_energy_B',
        'atomic_radius_X', 'molar_volume_X', 'ionization_energy_X',
        'MV_ratio', 'EN_diff'
        # 'TC_X' si existe y no está vacía
    ]
    feature_columns = [c for c in feature_columns if c in df.columns]

    # 3. Verificar columna objetivo
    if 'HSE06_bandgap' not in df.columns:
        logging.error("No se encontró columna 'HSE06_bandgap' en el dataset.")
        return

    # 4. Separar X e y
    X = df[feature_columns]
    y = df['HSE06_bandgap']

    # 5. Remover NaN
    valid_idx = X.dropna().index.intersection(y.dropna().index)
    X = X.loc[valid_idx]
    y = y.loc[valid_idx]

    if len(X) < 5:
        logging.error("No hay suficientes datos para entrenar el modelo simbólico.")
        return

    # 6. Instanciar y entrenar PySR
    model = PySRRegressor(
        niterations=40,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sqrt", "log", "exp"],
        populations=20,
        model_selection="best",
        progress=False
    )

    logging.info("Entrenando el modelo de regresión simbólica con PySR...")
    model.fit(X, y)

    # 7. Obtener la mejor ecuación como string
    best_equation = model.get_best()
    logging.info(f"Mejor ecuación simbólica para BandGap: {best_equation}")

    # 8. (Opcional) Ver todas las ecuaciones en un DataFrame
    eqs_df = model.equations  # <-- No se usa get_equations()
    # eqs_df contiene columnas como: 'equation', 'loss', 'complexity', etc.
    # Para verlas en orden de menor pérdida:
    eqs_df_sorted = eqs_df.sort_values("loss")
    print(eqs_df_sorted)

    # 9. Predecir y calcular error
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    logging.info(f"RMSE del modelo: {rmse:.3f}")
    logging.info(f"MAE del modelo: {mae:.3f}")

    # 10. Guardar predicciones en el DataFrame
    df['BandGap_pred'] = np.nan
    df.loc[valid_idx, 'BandGap_pred'] = y_pred
    df['error'] = df['BandGap_pred'] - df['HSE06_bandgap']

    # 11. Exportar a CSV final
    output_path = "data/processed/final_dataset.csv"
    df.to_csv(output_path, index=False)
    logging.info(f"Proceso completado. Archivo con predicciones guardado en {output_path}")

if __name__ == "__main__":
    main()