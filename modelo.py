import pandas as pd
import joblib
import os
import random

# ==============================================================================
# === CÓDIGO DE PRODUCCIÓN (Lo que se ejecuta al ser importado por Django) ===
# ==============================================================================

# --- 1. Cargar los modelos pre-entrenados ---
# Usamos os.path.join para crear rutas de archivo seguras que funcionan en cualquier SO
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ruta_regresion = os.path.join(BASE_DIR, 'modelo_regresion.pkl')
    ruta_clasificacion = os.path.join(BASE_DIR, 'modelo_clasificacion.pkl')

    modelo_regresion = joblib.load(ruta_regresion)
    modelo_clasificacion = joblib.load(ruta_clasificacion)
    print("Modelos cargados exitosamente desde archivos .pkl")

except FileNotFoundError:
    print("ADVERTENCIA: Archivos .pkl no encontrados. La app no podrá predecir.")
    print("Si estás en desarrollo, ejecuta 'python modelo.py' para entrenar y crear los modelos.")
    modelo_regresion = None
    modelo_clasificacion = None


# --- 2. Definir las funciones de negocio ---
# Estas funciones son ligeras y solo se definen, no se ejecutan hasta que son llamadas
def categorizar_nota(nota):
    if nota > 80:
        return "Alto rendimiento"
    elif nota >= 50:
        return "Promedio"
    else:
        return "Bajo rendimiento"

def generar_recomendaciones(estudiante_df):
    # Esta función necesita los percentiles, que son constantes. 
    # Podríamos calcularlos una vez en el script de entrenamiento y guardarlos,
    # pero por simplicidad, los definimos aquí como constantes.
    percentiles = {'asistencia': 25.0, 'participaciones': 25.0, 'evaluaciones': 25.0} # Valores aproximados

    recomendaciones = []
    asistencia_baja = estudiante_df["asistencia"].values[0] < percentiles['asistencia']
    participacion_baja = estudiante_df["participaciones"].values[0] < percentiles['participaciones']
    evaluaciones_baja = estudiante_df["evaluaciones"].values[0] < percentiles['evaluaciones']
    
    if participacion_baja and not asistencia_baja and not evaluaciones_baja:
        recomendaciones.append("¡Muy buen trabajo en asistencia y evaluaciones! Sin embargo, tu participación es extremadamente baja. Participar más en clase te ayudará a consolidar tu aprendizaje.")
    if asistencia_baja:
        recomendaciones.append("Tu asistencia es baja. Intenta asistir con más frecuencia para mejorar tu aprendizaje.")
    if participacion_baja:
        recomendaciones.append("Tu nivel de participación es críticamente bajo. Considera hablar más en clases, hacer preguntas o involucrarte en debates para fortalecer tu aprendizaje.")
    if evaluaciones_baja:
        recomendaciones.append("Tus evaluaciones muestran oportunidades de mejora. Puedes probar técnicas de estudio como la repetición activa.")
    if not recomendaciones:
        recomendaciones.append("¡Excelente trabajo! Tu rendimiento es sólido. Sigue así para mantener tu éxito académico.")
    return recomendaciones


# ==============================================================================
# === SCRIPT DE ENTRENAMIENTO (Solo se ejecuta con 'python modelo.py') ===
# ==============================================================================

if __name__ == "__main__":
    print("--- Ejecutando script en modo de entrenamiento ---")

    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

    # 1. Generar los datos (solo para entrenar)
    print("Generando 100,000 filas de datos de entrenamiento...")
    data = []
    for _ in range(100000):
        asistencia = random.randint(1, 100)
        participaciones = random.randint(1, 100)
        evaluaciones = random.randint(1, 100)
        nota_final = round((asistencia + participaciones + evaluaciones) / 3, 2)
        data.append({
            "asistencia": asistencia,
            "participaciones": participaciones,
            "evaluaciones": evaluaciones,
            "nota_final": nota_final
        })
    df = pd.DataFrame(data)
    df["rendimiento"] = df["nota_final"].apply(categorizar_nota)
    print("Datos generados.")

    # 2. Entrenar y guardar el Modelo de Regresión
    print("Entrenando modelo de Regresión Lineal...")
    X_reg = df[["asistencia", "participaciones", "evaluaciones"]]
    y_reg = df["nota_final"]
    x_train_reg, x_test_reg, y_train_reg, y_test_reg = train_test_split(X_reg, y_reg, test_size=0.2, random_state=123)
    
    modelo_reg_entrenado = LinearRegression()
    modelo_reg_entrenado.fit(x_train_reg, y_train_reg)
    joblib.dump(modelo_reg_entrenado, 'modelo_regresion.pkl')
    print("Modelo 'modelo_regresion.pkl' guardado.")

    # 3. Entrenar y guardar el Modelo de Clasificación
    print("Entrenando modelo de Clasificación (Random Forest)...")
    X_clf = df[["asistencia", "participaciones", "evaluaciones"]]
    y_clf = df["rendimiento"]
    X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(X_clf, y_clf, test_size=0.2, random_state=42)

    modelo_clf_entrenado = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo_clf_entrenado.fit(X_train_clf, y_train_clf)
    joblib.dump(modelo_clf_entrenado, 'modelo_clasificacion.pkl')
    print("Modelo 'modelo_clasificacion.pkl' guardado.")

    print("--- Entrenamiento finalizado ---")