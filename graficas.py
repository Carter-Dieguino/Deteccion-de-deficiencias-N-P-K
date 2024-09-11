import matplotlib.pyplot as plt
import numpy as np

# Datos para las gráficas
años_60 = np.arange(1, 4)
ingresos_60 = 2_064_902_784 * años_60
costos_totales_60 = 1_548_699_120 * años_60
beneficios_acumulados_60 = 516_203_664 * años_60

años_100 = np.arange(1, 3)
ingresos_100 = 3_438_596_800 * años_100
costos_totales_100 = 2_578_251_600 * años_100
beneficios_acumulados_100 = 860_345_200 * años_100

# Crear las gráficas
plt.figure(figsize=(14, 10))

# Gráfica de ingresos vs costos (60% y 100%)
plt.subplot(3, 1, 1)
plt.plot(años_60, ingresos_60, label='Ingresos Anuales (60%)', color='green')
plt.plot(años_60, costos_totales_60, label='Costos Totales Anuales (60%)', color='red')
plt.axvline(x=2.17, color='blue', linestyle='--', label='Punto de Equilibrio (60%)')
plt.xlabel('Años')
plt.ylabel('MXN')
plt.title('Ingresos vs Costos Totales Anuales al 60% de Capacidad Instalada')
plt.legend()

# Gráfica de beneficios acumulados y deuda (60%)
plt.subplot(3, 1, 2)
plt.plot(años_60, beneficios_acumulados_60, label='Beneficios Acumulados (60%)', color='blue')
plt.axhline(y=1_121_259_848.39, color='purple', linestyle='--', label='Deuda Total')
plt.axvline(x=2.17, color='orange', linestyle='--', label='Tiempo para Saldar la Deuda (60%)')
plt.xlabel('Años')
plt.ylabel('MXN')
plt.title('Beneficios Acumulados vs Deuda Total al 60% de Capacidad Instalada')
plt.legend()

# Gráfica de beneficios acumulados y deuda (100%)
plt.subplot(3, 1, 3)
plt.plot(años_100, beneficios_acumulados_100, label='Beneficios Acumulados (100%)', color='blue')
plt.axhline(y=1_121_259_848.39, color='purple', linestyle='--', label='Deuda Total')
plt.axvline(x=1.30, color='orange', linestyle='--', label='Tiempo para Saldar la Deuda (100%)')
plt.xlabel('Años')
plt.ylabel('MXN')
plt.title('Beneficios Acumulados vs Deuda Total al 100% de Capacidad Instalada')
plt.legend()

plt.tight_layout()
plt.show()
