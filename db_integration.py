import pyodbc
import requests
import datetime


def obtener_o_crear_id_equipo(cursor, nombre_equipo, pais_default="N/A"):

    try:
        sql_select = "SELECT Equipo_ID FROM Equipo WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_equipo)

        row = cursor.fetchone()

        if row:
            return row[0]

        else:
            print(f"  -> Equipo no encontrado: '{nombre_equipo}'. Creándolo...")

            sql_insert = """
                         INSERT INTO Equipo (Nombre, País, PartidosGanados, PartidosPerdidos)
                         VALUES (?, ?, 0, 0)}
                         """
            cursor.execute(sql_insert, (nombre_equipo, pais_default))


            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id = cursor.fetchone()[0]

            print(f"  -> Nuevo Equipo_ID creado: {nuevo_id}")

            return nuevo_id

    except pyodbc.Error as e:
        print(f"Error al obtener/crear equipo: {e}")
        return None


def obtener_o_crear_competicion_id(cursor, nombre_competicion):

    try:
        sql_select = "SELECT Competicion_ID FROM Competicion WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_competicion)
        row = cursor.fetchone()

        if row:
            return row[0]
        else:
            print(f"  -> Competición no encontrada: '{nombre_competicion}'. Creándola...")

            sql_insert = "INSERT INTO Competicion (Nombre, Deporte_ID) VALUES (?, 3)"
            cursor.execute(sql_insert, (nombre_competicion))

            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id = cursor.fetchone()[0]

            print(f"  -> Nueva Competicion_ID creada: {nuevo_id}")

            return nuevo_id

    except pyodbc.Error as e:
        print(f"Error al obtener o crear competición: {e}")
        return None


def obtener_o_crear_id_estadio(cursor, nombre_estadio, ciudad_default="N/A", pais_default="N/A"):
    """
    Busca un estadio por su nombre.
    Si existe, devuelve su Estadio_ID.
    Si no existe, lo crea (usando ciudad/país default) y devuelve el nuevo ID.
    """
    # Manejar el caso de que el nombre sea Nulo o N/A
    if not nombre_estadio or nombre_estadio.strip().upper() == "N/A":
        # Asumimos que ID=1 es 'Estadio No Especificado'
        # Podrías hacer un SELECT aquí para asegurarte, pero es menos eficiente
        return 1

    try:
        # 1. Buscar el estadio por nombre
        sql_select = "SELECT Estadio_ID FROM Estadio WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_estadio)
        row = cursor.fetchone()

        if row:
            # 2a. SÍ EXISTE: Devolver el ID encontrado
            return row[0]
        else:
            # 2b. NO EXISTE: Crear el estadio
            print(f"  -> Estadio no encontrado: '{nombre_estadio}'. Creándolo...")

            # (Estadio_ID es IDENTITY, no lo incluimos)
            sql_insert = "INSERT INTO Estadio (Nombre, Ciudad, País) VALUES (?, ?, ?)"
            cursor.execute(sql_insert, (nombre_estadio, ciudad_default, pais_default))

            # 3. Obtener el nuevo ID generado
            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id = cursor.fetchone()[0]

            print(f"  -> Nuevo Estadio_ID creado: {nuevo_id}")

            # 4. Devolver el nuevo ID
            return nuevo_id

    except pyodbc.Error as e:
        print(f"Error al obtener o crear estadio: {e}")
        return None  # O devolver el ID default (1) si prefieres
    except Exception as e:  # Captura otros errores (ej. nombre muy largo)
        print(f"Error inesperado al procesar estadio '{nombre_estadio}': {e}")
        return None  # O devolver el ID default (1)


def obtener_resultados():
    scraper_url = "http://127.0.0.1:5000/results"
    resultados_json = []

    try:
        print(f"Contactando al scraper en {scraper_url}...")

        response = requests.get(scraper_url)
        response.raise_for_status()
        resultados_json = response.json()

        print(f"¡Éxito! Se recibieron {len(resultados_json)} resultados del scraper.")

    except requests.exceptions.RequestException as e:
        print(f"ERROR AL CONECTAR CON EL SCRAPER: {e}")
        print("Asegúrate de que 'app.py' se esté ejecutando en otra terminal.")
        exit()

    print(resultados_json)

def agregar_partido(resultados_json):
    server = r'DESKTOP-BP55FHE\SQLEXPRESS'
    database = "modelo"


    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

    try:
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:

                for resultado in resultados_json:
                    equipo_local = resultado.get("local")
                    equipo_visitante = resultado.get("visitante")
                    goles_local = resultado.get("goles_local")
                    goles_visitante = resultado.get("goles_visitante")
                    nombre_competicion = resultado.get("competicion")
                    time_raw = resultado.get("time")
                    estadio = resultado.get("estadio")

                    competicion_id = obtener_o_crear_competicion_id(cursor, nombre_competicion)
                    equipo_local_id = obtener_o_crear_id_equipo(cursor, equipo_local)
                    equipo_visitante_id = obtener_o_crear_id_equipo(cursor, equipo_visitante)
                    estadio_id = obtener_o_crear_id_estadio(cursor, estadio)



                    if time_raw == ("Final"):
                        time = "Terminado"
                    elif time_raw[2:3] == ":":
                        time = "Pendiente"
                    else:
                        time = "Jugando"

                    sql_insert = """
                        INSERT INTO Partido (Estado, ResultadoLocal, ResultadoVisitante, Fecha, Competición_ID,
                        Estadio_ID, EquipoLocal_ID, EquipoVisitante_ID, FechaFinEstimada) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, SELECT DATEADD(hour, 2, GETDATE());)
                            
                    """

                    cursor.execute(sql_insert, (time, goles_local,goles_visitante, competicion_id, estadio_id, equipo_local_id, equipo_visitante_id))


    except pyodbc.Error as e:
        print(e)