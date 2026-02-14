# Ejercicio de programación 2 y análisis estático

## Descripción general
Este proyecto implementa un programa en Python (`computeSales.py`) que calcula
el costo total de ventas a partir de un catálogo de productos en formato JSON.

## Estructura del proyecto
A01366730_A5.2/
├── source/
│ └── computeSales.py
├── data/
│ ├── TC1/
│ │ ├── TC1.ProductList.json
│ │ └── TC1.Sales.json
│ ├── TC2/
│ │ ├── TC2.ProductList.json
│ │ └── TC2.Sales.json
│ └── TC3/
│ ├── TC3.ProductList.json
│ └── TC3.Sales.json
│
├── results/
│ ├── TC1_SalesResults.txt
│ ├── TC2_SalesResults.txt
│ ├── TC3_SalesResults.txt
│ └── static_analysis/
│ ├── flake8_report.txt
│ └── pylint_report.txt
└── README.md

## Ejecución del programa

Se espera que el programa se ejecute desde el directorio raíz (A01366730_A5.2)

```bash
python source/computeSales.py data/TC1/TC1.ProductList.json data/TC1/TC1.Sales.json
```

```bash
python source/computeSales.py data/TC2/TC2.ProductList.json data/TC2/TC2.Sales.json
```

```bash
python source/computeSales.py data/TC3/TC3.ProductList.json data/TC3/TC3.Sales.json
```
