#pip install pandas numpy scikit-learn
import random
import numpy as np
import pandas as pd
import warnings
from sklearn.preprocessing import LabelEncoder
from scipy.stats import norm, skew
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics
warnings.filterwarnings('ignore')


# Generar los datos
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

# leer datos en pandas
df =pd.DataFrame(data)

# Función para categorizar rendimiento
def categorizar_nota(nota):
    if nota > 80:
        return "Alto rendimiento"
    elif nota >= 50:
        return "Promedio"
    else:
        return "Bajo rendimiento"

# Aplicar la función a la columna 'nota_final'
df["rendimiento"] = df["nota_final"].apply(categorizar_nota)
#print(df)








#-------------------- PROCESAMIENTO DE DATA ----------------------------------------
# cuenta las categorias del rendimiento
#print(df.rendimiento.value_counts())

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import seaborn as sns
    # hace un grafico en barras sobre el rendimiento
    df.rendimiento.value_counts(normalize=True).plot(kind ="bar", color=["blue", "red"])
    #plt.show()

# muestra los tipos de datos de las variables de la data
#print(df.info())

# muestra la cantidad de nulos de cada variable
#print(df.isnull().sum())


# Separar variables independientes (X) y la variable dependiente (y)
X = df[["asistencia", "participaciones", "evaluaciones"]]  # Características
y = df["nota_final"]  # Variable objetivo

# separar los datos de entrenamiento y los datos de prueba
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)
#print(y_train.head())

#--------------------- REGRESION LINEAL -----------------------
# creamos el modelo de regresion lineal
modelo = LinearRegression()
# entrenamos el modelo con los datos de entrenamiento
modelo.fit(x_train, y_train)

# realizar predicciones con los datos de prueba
y_pred = modelo.predict(x_test)
#print(y_pred)


# Calcular métricas adecuadas para regresión
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
# mostrar los resultados de las metricas
print(f"MSE: {mse}")
print(f"R² Score: {r2}")

# establecer el nuevo dato que el modelo aun no conoce
nuevo_dato = pd.DataFrame({
    "asistencia": [100],   
    "participaciones": [89],
    "evaluaciones": [50]
})

# predecir con el dato nuevo
prediccion = modelo.predict(nuevo_dato)
print(f"Nota final predicha: {prediccion[0]}")


#------------------- CLASIFICADOR RANDOM FOREST ------------------------
# separemos las variables dependientes e independientes
X = df[["asistencia", "participaciones", "evaluaciones"]]  # Características
y = df["rendimiento"]  # Variable de clasificación


# Dividir datos en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crear el modelo
modelo_clasificacion = RandomForestClassifier(n_estimators=100, random_state=42)
# entrenar el modelo
modelo_clasificacion.fit(X_train, y_train)

# predecir con los datos de prueba
y_predi = modelo_clasificacion.predict(X_test)

# Evaluación del modelo
print("Valor de accuracy: ",metrics.accuracy_score(y_test, y_predi))

score = modelo_clasificacion.score(X_test, y_test)
print(f"Precisión del modelo: {score:.2f}")
#print(df.rendimiento.value_counts())

# predecir el modelo con datos que aun no conoce
prediccion = modelo_clasificacion.predict(nuevo_dato)
print(f"Rendimiento predicho: {prediccion[0]}")



#--------------------- RECOMENDACIONES --------------------------------
# Calcular percentiles de cada característica en el conjunto de datos
percentiles = df[["asistencia", "participaciones", "evaluaciones"]].quantile([0.25, 0.5, 0.75])

def generar_recomendaciones(estudiante):
    recomendaciones = []

    asistencia_baja = estudiante["asistencia"].values[0] < percentiles.loc[0.25, "asistencia"]
    participacion_baja = estudiante["participaciones"].values[0] < percentiles.loc[0.25, "participaciones"] or estudiante["participaciones"].values[0] <= 5
    evaluaciones_baja = estudiante["evaluaciones"].values[0] < percentiles.loc[0.25, "evaluaciones"]

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

# Probar con los datos actuales
recomendaciones = generar_recomendaciones(nuevo_dato)

if __name__ == "__main__":
    print("Recomendaciones:")
    for r in recomendaciones:
        print(f"- {r}")