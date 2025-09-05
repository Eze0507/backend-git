# ERP para taller mecanico
## clonar repositorio
git clone [repository url]

## entorno virtual
### crear entorno virtual
python -m venv env
### activar En Windows
.\env\Scripts\activate
### activar En macOS/Linux
source env/bin/activate

## instalar dependencias
pip install -r requirements.txt

## Configura el proyecto:
Crea un archivo .env en la raíz del proyecto y rellénalo siguiendo el archivo .env.example.

## migraciones para la base de datos
python manage.py migrate

## inicar servidor
python manage.py runserver
