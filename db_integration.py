import pyodbc
import requests
from datetime import datetime

MAX_NAME_LENGTH = 50
DEFAULT_STADIUM_ID = 1
DEFAULT_DEPORTE_ID = 1

def obtener_o_crear_id_equipo(cursor, nombre_equipo, pais_default="N/A"):
    if not nombre_equipo or not nombre_equipo.strip(): return None
    if len(nombre_equipo) > MAX_NAME_LENGTH: nombre_equipo = nombre_equipo[:MAX_NAME_LENGTH]
    try:
        sql_select = "SELECT Equipo_ID FROM Equipo WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_equipo)
        row = cursor.fetchone()
        if row: return row[0]
        else:
            print(f"  -> Equipo no encontrado: '{nombre_equipo}'. Creándolo...")
            sql_insert = "INSERT INTO Equipo (Nombre, País, PartidosGanados, PartidosPerdidos) VALUES (?, ?, 0, 0)"
            try: cursor.execute(sql_insert, (nombre_equipo, pais_default))
            except pyodbc.Error as insert_err:
                print(f"    -> ERROR DURANTE INSERT Equipo: {insert_err}")
                cursor.execute(sql_select, nombre_equipo); row_check = cursor.fetchone()
                if row_check: return row_check[0]
                return None
            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id_row = cursor.fetchone()
            if nuevo_id_row and nuevo_id_row[0] is not None:
                 return int(nuevo_id_row[0])
            else:
                 cursor.execute(sql_select, nombre_equipo); row_check = cursor.fetchone()
                 if row_check: return row_check[0]
                 return None
    except Exception as e: print(f"Error procesando equipo '{nombre_equipo}': {e}"); return None

def obtener_o_crear_competicion_id(cursor, nombre_competicion, id_deporte_default=DEFAULT_DEPORTE_ID):
    if not nombre_competicion or not nombre_competicion.strip(): return None
    if len(nombre_competicion) > MAX_NAME_LENGTH: nombre_competicion = nombre_competicion[:MAX_NAME_LENGTH]
    try:
        sql_select = "SELECT Competicion_ID FROM Competicion WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_competicion)
        row = cursor.fetchone()
        if row: return row[0]
        else:
            print(f"  -> Competición no encontrada: '{nombre_competicion}'. Creándola...")
            sql_insert = "INSERT INTO Competicion (Nombre, Deporte_ID) VALUES (?, ?)"
            try: cursor.execute(sql_insert, (nombre_competicion, id_deporte_default))
            except pyodbc.Error as insert_err:
                 print(f"    -> ERROR DURANTE INSERT Competicion: {insert_err}")
                 cursor.execute(sql_select, nombre_competicion); row_check = cursor.fetchone()
                 if row_check: return row_check[0]
                 return None
            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id_row = cursor.fetchone()
            if nuevo_id_row and nuevo_id_row[0] is not None:
                return int(nuevo_id_row[0])
            else:
                 cursor.execute(sql_select, nombre_competicion); row_check = cursor.fetchone()
                 if row_check: return row_check[0]
                 return None
    except Exception as e: print(f"Error procesando competición '{nombre_competicion}': {e}"); return None


def obtener_o_crear_id_estadio(cursor, nombre_estadio, ciudad_default="N/A", pais_default="N/A"):
    if not nombre_estadio or nombre_estadio.strip().upper() == "N/A" or nombre_estadio.strip() == '': return DEFAULT_STADIUM_ID
    if len(nombre_estadio) > MAX_NAME_LENGTH: nombre_estadio = nombre_estadio[:MAX_NAME_LENGTH]
    try:
        sql_select = "SELECT Estadio_ID FROM Estadio WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_estadio)
        row = cursor.fetchone()
        if row: return row[0]
        else:
            print(f"  -> Estadio no encontrado: '{nombre_estadio}'. Creándolo...")
            sql_insert = "INSERT INTO Estadio (Nombre, Ciudad, País) VALUES (?, ?, ?)"
            try: cursor.execute(sql_insert, (nombre_estadio, ciudad_default, pais_default))
            except pyodbc.Error as insert_err:
                 print(f"    -> ERROR DURANTE INSERT Estadio: {insert_err}. Usando ID default.")
                 cursor.execute(sql_select, nombre_estadio); row_check = cursor.fetchone()
                 if row_check: return row_check[0]
                 return DEFAULT_STADIUM_ID
            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id_row = cursor.fetchone()
            if nuevo_id_row and nuevo_id_row[0] is not None:
                return int(nuevo_id_row[0])
            else:
                 cursor.execute(sql_select, nombre_estadio); row_check = cursor.fetchone()
                 if row_check: return row_check[0]
                 return DEFAULT_STADIUM_ID
    except Exception as e: print(f"Error procesando estadio '{nombre_estadio}': {e}. Usando ID default."); return DEFAULT_STADIUM_ID

def agregar_equipo_a_competicion_si_no_existe(cursor, equipo_id, competicion_id):
    if not equipo_id or not competicion_id: return
    try:
        sql_check = "SELECT 1 FROM EquipoEnComp WHERE Equipo_ID = ? AND Competicion_ID = ?"
        cursor.execute(sql_check, (equipo_id, competicion_id))
        existe = cursor.fetchone()
        if not existe:
            print(f"  -> Vinculando Equipo ID {equipo_id} a Competición ID {competicion_id}...")
            sql_insert = "INSERT INTO EquipoEnComp (Equipo_ID, Competicion_ID) VALUES (?, ?)"
            try: cursor.execute(sql_insert, (equipo_id, competicion_id))
            except pyodbc.Error as insert_err:
                 if 'duplicate key' not in str(insert_err).lower() and 'unique constraint' not in str(insert_err).lower():
                      print(f"    -> ERROR al insertar vínculo EquipoEnComp: {insert_err}")
            except Exception as other_insert_err: print(f"    -> ERROR NO SQL al insertar vínculo EquipoEnComp: {other_insert_err}")
    except Exception as general_e: print(f"Error inesperado al vincular equipo-competición: {general_e}")


def obtener_resultados():
    scraper_url = "http://127.0.0.1:5000/results"
    try:
        print(f"Contactando al scraper en {scraper_url}...")
        response = requests.get(scraper_url, timeout=300)
        response.raise_for_status()
        resultados_json = response.json()
        if not isinstance(resultados_json, list):
             print(f"ERROR: La respuesta del scraper no es una lista JSON. Respuesta: {resultados_json}")
             return None
        print(f"¡Éxito! Se recibieron {len(resultados_json)} resultados del scraper.")
        return resultados_json
    except requests.exceptions.Timeout: print(f"ERROR SCRAPER: Timeout."); return None
    except requests.exceptions.RequestException as e: print(f"ERROR SCRAPER: {e}"); return None
    except requests.exceptions.JSONDecodeError: print(f"ERROR: Respuesta no JSON."); return None


def agregar_partido(resultados_json):
    server = r'DESKTOP-BP55FHE\SQLEXPRESS'
    database = "BetNova"
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    connection = None
    try:
        connection = pyodbc.connect(connection_string, autocommit=False)
        with connection.cursor() as cursor:
            print("Iniciando proceso de agregar/actualizar partidos...")
            partidos_procesados, partidos_insertados, partidos_actualizados = 0, 0, 0

            for resultado in resultados_json:
                 try:
                    if not isinstance(resultado, dict): continue
                    nombre_local = resultado.get("local")
                    nombre_visitante = resultado.get("visitante")
                    goles_local_str = resultado.get("goles_local")
                    goles_visitante_str = resultado.get("goles_visitante")
                    nombre_competicion = resultado.get("liga")
                    time_raw = resultado.get("tiempo")
                    nombre_estadio = resultado.get("estadio")
                    if not all([nombre_local, nombre_visitante, nombre_competicion]): continue
                    if goles_local_str is None or goles_visitante_str is None: continue

                    competicion_id = obtener_o_crear_competicion_id(cursor, nombre_competicion)
                    equipo_local_id = obtener_o_crear_id_equipo(cursor, nombre_local)
                    equipo_visitante_id = obtener_o_crear_id_equipo(cursor, nombre_visitante)
                    estadio_id = obtener_o_crear_id_estadio(cursor, nombre_estadio)

                    if competicion_id is None or equipo_local_id is None or equipo_visitante_id is None:
                        print(f"  -> Saltando: IDs inválidos (C:{competicion_id}, L:{equipo_local_id}, V:{equipo_visitante_id})")
                        continue

                    agregar_equipo_a_competicion_si_no_existe(cursor, equipo_local_id, competicion_id)
                    agregar_equipo_a_competicion_si_no_existe(cursor, equipo_visitante_id, competicion_id)

                    try:
                        goles_local_int = 0 if goles_local_str == '-' else int(goles_local_str)
                        goles_visit_int = 0 if goles_visitante_str == '-' else int(goles_visitante_str)
                    except (ValueError, TypeError):
                         print(f"  -> ERROR DE DATOS: Goles inválidos. Usando 0.")
                         goles_local_int, goles_visit_int = 0, 0
                    estado_actualizado = estandarizar_estado_partido(time_raw)

                    print(f"\n--- Partido: {nombre_local} vs {nombre_visitante} ---")
                    print(f"IDs -> C:{competicion_id}, L:{equipo_local_id}, V:{equipo_visitante_id}, E:{estadio_id}")
                    print(f"Estado Scraper (limpio): '{estado_actualizado}' | Goles: {goles_local_int}-{goles_visit_int}")

                    sql_find_partido = """
                                       SELECT Partido_ID, Estado, ResultadoLocal, ResultadoVisitante
                                       FROM Partido WHERE EquipoLocal_ID = ? AND EquipoVisitante_ID = ?
                                         AND Competicion_ID = ? AND Estado != 'finalizado'
                                       """
                    cursor.execute(sql_find_partido, (equipo_local_id, equipo_visitante_id, competicion_id))
                    partido_existente = cursor.fetchone()

                    if partido_existente:
                        partido_id_a_actualizar = partido_existente.Partido_ID
                        estado_previo = partido_existente.Estado.strip() if partido_existente.Estado else 'desconocido'
                        goles_local_previo = partido_existente.ResultadoLocal
                        goles_visit_previo = partido_existente.ResultadoVisitante
                        print(f"Estado en BD (previo): '{estado_previo}' | Goles BD: {goles_local_previo}-{goles_visit_previo}")

                        if (estado_previo != estado_actualizado or
                            goles_local_int != goles_local_previo or
                            goles_visit_int != goles_visit_previo):

                            print(f"  -> Actualizando partido existente ID={partido_id_a_actualizar}")
                            sql_update = "UPDATE Partido SET Estado = ?, ResultadoLocal = ?, ResultadoVisitante = ?"
                            current_py_time = datetime.now()
                            params_update = [estado_actualizado, goles_local_int, goles_visit_int]
                            commit_now = False

                            print(f"DEBUG: Comparando: estado_actualizado=='{estado_actualizado}' vs 'finalizado' -> {estado_actualizado == 'finalizado'}")
                            print(f"DEBUG: Comparando: estado_previo=='{estado_previo}' vs 'finalizado' -> {estado_previo != 'finalizado'}")
                            print(f"DEBUG: Condición completa -> {(estado_actualizado == 'finalizado' and estado_previo != 'finalizado')}")

                            if estado_actualizado == 'finalizado' and estado_previo != 'finalizado':
                                print(">>> CONDICIÓN CUMPLIDA: Se añadirá FechaFinEstimada <<<")
                                sql_update += ", FechaFinEstimada = ?"
                                params_update.append(current_py_time)
                                commit_now = True
                            else:
                                print(">>> Condición NO cumplida para FechaFinEstimada <<<")

                            sql_update += " WHERE Partido_ID = ?"
                            params_update.append(partido_id_a_actualizar)

                            print(f"Ejecutando UPDATE: {sql_update}")
                            print(f"Con parámetros: {tuple(params_update)}")
                            cursor.execute(sql_update, tuple(params_update))
                            partidos_actualizados += 1

                            if commit_now:
                                print("--- DEBUG: Forzando commit AHORA después de actualizar FechaFinEstimada ---")
                                connection.commit()

                            if estado_actualizado == 'finalizado' and estado_previo != 'finalizado':
                                ganador_id, perdedor_id = (None, None)
                                if goles_local_int > goles_visit_int:   ganador_id, perdedor_id = equipo_local_id, equipo_visitante_id
                                elif goles_visit_int > goles_local_int: ganador_id, perdedor_id = equipo_visitante_id, equipo_local_id
                                if ganador_id and perdedor_id:
                                    cursor.execute("UPDATE Equipo SET PartidosGanados = PartidosGanados + 1 WHERE Equipo_ID = ?", ganador_id)
                                    cursor.execute("UPDATE Equipo SET PartidosPerdidos = PartidosPerdidos + 1 WHERE Equipo_ID = ?", perdedor_id)
                        else:
                            print(f"  -> Sin cambios detectados. No se actualiza.")

                    else:
                         sql_check_finished = "SELECT 1 FROM Partido WHERE EquipoLocal_ID = ? AND EquipoVisitante_ID = ? AND Competicion_ID = ? AND Estado = 'finalizado'"
                         cursor.execute(sql_check_finished, (equipo_local_id, equipo_visitante_id, competicion_id))
                         ya_finalizado = cursor.fetchone()
                         if not ya_finalizado:
                            print(f"  -> Insertando nuevo partido: {nombre_local} vs {nombre_visitante}")
                            sql_insert = "INSERT INTO Partido (Estado, ResultadoLocal, ResultadoVisitante, Fecha, Competicion_ID, Estadio_ID, EquipoLocal_ID, EquipoVisitante_ID, FechaFinEstimada) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, ?, NULL)"
                            datos_partido = (estado_actualizado, goles_local_int, goles_visit_int, competicion_id, estadio_id, equipo_local_id, equipo_visitante_id)
                            cursor.execute(sql_insert, datos_partido)
                            partidos_insertados += 1
                         else:
                            print(f"  -> Saltando inserción: Partido finalizado ya existe.")

                    partidos_procesados += 1

                 except (TypeError, ValueError) as data_err: print(f"  -> ERROR DE DATOS en bucle: {data_err}")
                 except pyodbc.Error as db_err: print(f"  -> ERROR DE BD en bucle: {db_err}")
                 except Exception as loop_err: print(f"  -> ERROR INESPERADO en bucle: {loop_err}")

            print(f"\nBucle finalizado. Procesados: {partidos_procesados}, Insertados: {partidos_insertados}, Actualizados: {partidos_actualizados}.")
            # print("Haciendo commit final a la base de datos...") # Final commit only if not using immediate commit
            # connection.commit()
            print("¡Proceso completado!")

    except pyodbc.Error as e:
        print(f"ERROR DE CONEXIÓN A LA BASE DE DATOS: {e}")
        if connection:
            try: connection.rollback(); print("Rollback intentado por error de conexión/proceso.")
            except pyodbc.Error as rb_err: print(f"Error durante rollback: {rb_err}")
    except Exception as general_e:
        print(f"Ha ocurrido un error inesperado general: {general_e}")
        if connection:
            try: connection.rollback(); print("Rollback intentado por error general.")
            except pyodbc.Error as rb_err: print(f"Error durante rollback: {rb_err}")
    finally:
         if connection:
             connection.close()
             print("Conexión a BD cerrada.")

def estandarizar_estado_partido(tiempo_crudo):
    if not tiempo_crudo: return 'pendiente'
    estado = str(tiempo_crudo).lower().strip()
    if estado.startswith('fin') or estado.startswith('final') or estado == 'penales' or estado == 'aband.' or estado == 'terminado':
        return 'finalizado'
    palabras_jugando = ["'", "et", "e.t.", "entretiempo", "ht", "pen.", "en curso", "descanso"]
    if any(palabra in estado for palabra in palabras_jugando): return 'jugando'
    palabras_pendiente = [":", "programado", "susp.", "posp.", "apl.", "cancelado"]
    if any(palabra in estado for palabra in palabras_pendiente): return 'pendiente'
    return 'pendiente'

if __name__ == "__main__":
    datos = obtener_resultados()
    if datos:
        agregar_partido(datos)
    else:
        print("No se recibieron datos del scraper. Finalizando.")