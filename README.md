# Evallo
Ontología evaluación recursos LOD, visuañlización y webscrapper

Para desplegar el proyecto se deben seguir los siguientes pasos:
1. Descargar el instalador de apache Jena en https://jena.apache.org/download/index.cgi
2. Instalar el servidor apache Jena asegurando que quede disponible a través de protocolo https
3. Importar el archivo de la Ontologia EvalLOD-merged.owl
4. Desplegar el codigo del scrapper en una función de Azure o importar el notebook para realizar pruebas de ejecución del scrapper
5. Desplegar la visualización en cualquier servidor de aplicaciones, bucket o storage acccount que permita conexión a través de https
6. Actualizar todas las URL marcadas en el código fuente por las url de despliegue.
