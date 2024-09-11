import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.linear_model import Ridge, Lasso
from statsmodels.robust.robust_linear_model import RLM
import warnings

# Suprimir advertencias
#warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.simplefilter(action='ignore', category=UserWarning)

# Datos
data = {
    'Municipio': ['Almoloya', 'Apan', 'Cardonal', 'Chapatongo', 'Cuautepec de Hinojosa', 'Emiliano Zapata', 'Ixmiquilpan', 'Metztitlán', 'Tepeapulco', 'Tepeji del Río de Ocampo', 'Tepetitlán', 'Tlanalapa', 'Tula de Allende', 'Villa de Tezontepec', 'Zempoala'],
    'Rendimiento (ton/ha)': [1.38, 1.78, 0.62, 0.98, 0.95, 1.93, 0.89, 0.49, 1.87, 0.36, 0.38, 1.45, 0.48, 0.65, 1.00],
    'Erosión (ton/ha)': [57.80, 110.12, 346.93, 51.71, 126.41, 57.13, 5.29, 123.69, 25.55, 35.83, 68.44, 26.27, 26.09, 84.75, 21.86],
    'Fertilización del suelo': [87.94, 90.91, 91.89, 56.37, 75.09, 90.92, 68.02, 86.26, 86.26, 60.19, 69.38, 55.14, 43.36, 43.36, 41.31],
    'Herbicidas': [82.45, 82.01, 44.64, 35.96, 43.01, 83.77, 38.77, 78.31, 78.31, 53.62, 48.91, 38.48, 34.41, 34.41, 35.83],
    'Asistencia técnica para la producción (%)': [4.65, 6.62, 4.64, 1.29, 1.11, 7.91, 2.78, 3.24, 8.88, 1.40, 3.44, 0.71, 4.41, 5.03, 3.25],
    'Acceso a programas (%)': [52.98, 46.73, 47.67, 45.71, 30.94, 51.77, 9.27, 15.82, 53.72, 30.15, 26.48, 29.71, 41.76, 41.76, 51.95],
    'Productores con acceso a créditos': [106.00, 206.00, 43.00, 19.00, 101.00, 89.00, 257.00, 40.00, 132.00, 28.00, 17.00, 13.00, 39.00, 62.00, 61.00]
}

df = pd.DataFrame(data)
X = df[['Rendimiento (ton/ha)', 'Fertilización del suelo', 'Herbicidas', 'Asistencia técnica para la producción (%)', 'Acceso a programas (%)', 'Productores con acceso a créditos']]
y = df['Erosión (ton/ha)']
X = sm.add_constant(X)

# Modelo de regresión lineal múltiple
model_lm = sm.OLS(y, X).fit()
print("Modelo de Regresión Lineal Múltiple:\n", model_lm.summary())

# Regresión robusta
model_robust = RLM(y, X).fit()
print("\nModelo de Regresión Robusta:\n", model_robust.summary())

# Regresión Ridge
ridge = Ridge(alpha=1.0)
ridge.fit(X, y)
print("\nCoeficientes de Regresión Ridge:\n", ridge.coef_)

# Regresión Lasso
lasso = Lasso(alpha=0.1)
lasso.fit(X, y)
print("\nCoeficientes de Regresión Lasso:\n", lasso.coef_)

# Regresión con transformaciones de variables
X_transformed = np.log(X + 1)
model_transformed = sm.OLS(np.log(y + 1), X_transformed).fit()
print("\nModelo de Regresión con Transformaciones de Variables:\n", model_transformed.summary())

input("Presione Enter para cerrar...")
