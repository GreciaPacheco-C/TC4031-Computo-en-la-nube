# Actividad 4.2 – Pruebas y Calidad

Esta carpeta del  repositorio contiene la implementación de los tres ejercicios de programación solicitados en la **Actividad 4.2**, desarrollados en **Python** y organizados por programa (P1, P2 y P3).  
Cada programa cumple con el estándar de codificación **PEP 8**, incluye casos de prueba y fue validado utilizando **pylint**.

---

## Estructura general del repositorio

Cada programa se organiza de la siguiente forma:

P#
├─ source/
├─ data/
├─ results/


### Descripción de carpetas

- **source/**  
  Contiene el código fuente del programa en Python.

- **data/**  
  Contiene los archivos de entrada utilizados como **casos de prueba** (`TC1.txt`, `TC2.txt`, ..., `TC7.txt`).

- **results/**  
  Contiene la evidencia de ejecución:
  - Archivos de salida generados por el programa.
  - El archivo `pylint.txt` con el reporte de análisis estático.

---

## Ejecución de los programas

⚠️ **Los programas deben ejecutarse desde la carpeta del programa correspondiente (P1, P2 o P3).**

### Ejemplo de ejecución para P2

Desde la carpeta **P2**, ejecutar un solo caso de prueba:

```bash
python source/convertNumbers.py data/TC1.txt
```
Desde la carpeta **P2**, ejecutar todos los casos de prueba:

```bash
python source/convertNumbers.py data --all
```

