from pypdf import PdfWriter
import os

# Carpeta donde están los PDF
pasta = r"C:\Users\mapen\Downloads\Diario Obras Confusao"

# Archivo de salida
saida = os.path.join(pasta, "PDF_Unido.pdf")

# Crea el objeto que unirá los PDF
merger = PdfWriter()

# Obtiene todos los PDF de la carpeta y los ordena alfabéticamente
arquivos = sorted(
    [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
)

# Agrega cada PDF
for arquivo in arquivos:
    caminho = os.path.join(pasta, arquivo)
    merger.append(caminho)

# Guarda el resultado
with open(saida, "wb") as f:
    merger.write(f)

merger.close()

print(f"PDF creado correctamente: {saida}")