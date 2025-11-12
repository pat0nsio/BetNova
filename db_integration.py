import pyodbc
import requests

MAX_NAME_LENGTH = 50
DEFAULT_DEPORTE_ID = 1


def obtener_o_crear_id_equipo(cursor, nombre_equipo):
    if not nombre_equipo or not nombre_equipo.strip(): return None
    if len(nombre_equipo) > MAX_NAME_LENGTH: nombre_equipo = nombre_equipo[:MAX_NAME_LENGTH]
    try:
        sql_select = "SELECT Equipo_ID FROM Equipo WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_equipo)
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            sql_insert = "INSERT INTO Equipo (Nombre, PartidosGanados, PartidosPerdidos) VALUES (?, 0, 0)"

            try:
                cursor.execute(sql_insert, (nombre_equipo,))
            except pyodbc.Error as insert_err:
                print(f"Error insertando equipo '{nombre_equipo}': {insert_err}")
                cursor.execute(sql_select, nombre_equipo);
                row_check = cursor.fetchone()
                if row_check: return row_check[0]
                return None

            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id_row = cursor.fetchone()
            if nuevo_id_row and nuevo_id_row[0] is not None:
                return int(nuevo_id_row[0])
            else:
                cursor.execute(sql_select, nombre_equipo);
                row_check = cursor.fetchone()
                if row_check: return row_check[0]
                return None
    except Exception as e:
        print(f"Error procesando equipo '{nombre_equipo}': {e}");
        return None

def obtener_o_crear_competicion_id(cursor, nombre_competicion, id_deporte_default=DEFAULT_DEPORTE_ID):
    if not nombre_competicion or not nombre_competicion.strip(): return None
    if len(nombre_competicion) > MAX_NAME_LENGTH: nombre_competicion = nombre_competicion[:MAX_NAME_LENGTH]
    try:
        sql_select = "SELECT Competicion_ID FROM Competicion WHERE Nombre = ?"
        cursor.execute(sql_select, nombre_competicion)
        row = cursor.fetchone()
        if row: return row[0]
        else:
            print(f"Creando competición: '{nombre_competicion}'...")
            sql_insert = "INSERT INTO Competicion (Nombre, Deporte_ID) VALUES (?, ?)"
            try: cursor.execute(sql_insert, (nombre_competicion, id_deporte_default))
            except pyodbc.Error as insert_err:
                 print(f"Error insertando competición '{nombre_competicion}': {insert_err}")
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
    except Exception as e:
        print(f"Error procesando competición '{nombre_competicion}': {e}"); return None

def agregar_equipo_a_competicion_si_no_existe(cursor, equipo_id, competicion_id):
    if not equipo_id or not competicion_id: return
    try:
        sql_check = "SELECT 1 FROM EquipoEnComp WHERE Equipo_ID = ? AND Competicion_ID = ?"
        cursor.execute(sql_check, (equipo_id, competicion_id))
        existe = cursor.fetchone()
        if not existe:
            sql_insert = "INSERT INTO EquipoEnComp (Equipo_ID, Competicion_ID) VALUES (?, ?)"
            try: cursor.execute(sql_insert, (equipo_id, competicion_id))
            except pyodbc.Error as insert_err:
                 if 'duplicate key' not in str(insert_err).lower() and 'unique constraint' not in str(insert_err).lower():
                      print(f"Error insertando vínculo EquipoEnComp ({equipo_id}-{competicion_id}): {insert_err}")
            except Exception as other_insert_err:
                 print(f"Error (no SQL) insertando vínculo EquipoEnComp ({equipo_id}-{competicion_id}): {other_insert_err}")
    except Exception as general_e:
        print(f"Error vinculando equipo-competición ({equipo_id}-{competicion_id}): {general_e}")


def obtener_resultados():
    scraper_url = "http://127.0.0.1:5000/results"
    try:
        print(f"Contactando scraper: {scraper_url}...")
        response = requests.get(scraper_url, timeout=300)
        response.raise_for_status()
        resultados_json = response.json()
        if not isinstance(resultados_json, list):
             print(f"Error: Scraper no devolvió una lista JSON.")
             return None
        print(f"Éxito scraper: {len(resultados_json)} resultados.")
        return resultados_json
    except requests.exceptions.Timeout: print(f"Error: Timeout conectando al scraper."); return None
    except requests.exceptions.RequestException as e: print(f"Error: Conexión scraper: {e}"); return None
    except requests.exceptions.JSONDecodeError: print(f"Error: Scraper no devolvió JSON válido."); return None


def agregar_partido(resultados_json):
    server = input("Server: ")
    database = "BetNova"
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    connection = None
    try:
        connection = pyodbc.connect(connection_string, autocommit=False)
        with connection.cursor() as cursor:
            processed, inserted, updated = 0, 0, 0

            for resultado in resultados_json:
                try:
                    if not isinstance(resultado, dict): continue
                    nombre_local = resultado.get("local")
                    nombre_visitante = resultado.get("visitante")
                    goles_local_str = resultado.get("goles_local")
                    goles_visitante_str = resultado.get("goles_visitante")
                    nombre_competicion = resultado.get("liga")
                    time_raw = resultado.get("tiempo")

                    if not all([nombre_local, nombre_visitante, nombre_competicion]): continue
                    if goles_local_str is None or goles_visitante_str is None: continue

                    competicion_id = obtener_o_crear_competicion_id(cursor, nombre_competicion)
                    equipo_local_id = obtener_o_crear_id_equipo(cursor, nombre_local)
                    equipo_visitante_id = obtener_o_crear_id_equipo(cursor, nombre_visitante)

                    if competicion_id is None or equipo_local_id is None or equipo_visitante_id is None:
                        continue

                    agregar_equipo_a_competicion_si_no_existe(cursor, equipo_local_id, competicion_id)
                    agregar_equipo_a_competicion_si_no_existe(cursor, equipo_visitante_id, competicion_id)

                    try:
                        goles_local_int = 0 if goles_local_str == '-' else int(goles_local_str)
                        goles_visit_int = 0 if goles_visitante_str == '-' else int(goles_visitante_str)
                    except (ValueError, TypeError):
                        goles_local_int, goles_visit_int = 0, 0

                    estado_actualizado = estandarizar_estado_partido(time_raw)


                    sql_find_partido = """
                                       SELECT Partido_ID, Estado, ResultadoLocal, ResultadoVisitante
                                       FROM Partido \
                                       WHERE EquipoLocal_ID = ? \
                                         AND EquipoVisitante_ID = ? \
                                         AND Competicion_ID = ? \
                                         AND Estado != 3 \
                                       """
                    cursor.execute(sql_find_partido, (equipo_local_id, equipo_visitante_id, competicion_id))
                    partido_existente = cursor.fetchone()

                    if partido_existente:
                        partido_id = partido_existente.Partido_ID
                        estado_previo = partido_existente.Estado
                        goles_local_prev = partido_existente.ResultadoLocal
                        goles_visit_prev = partido_existente.ResultadoVisitante

                        if (estado_previo != estado_actualizado or
                                goles_local_int != goles_local_prev or
                                goles_visit_int != goles_visit_prev):

                            sql_update = """
                                         UPDATE Partido \
                                         SET Estado             = ?, \
                                             ResultadoLocal     = ?, \
                                             ResultadoVisitante = ?
                                         WHERE Partido_ID = ? \
                                         """
                            params = (estado_actualizado, goles_local_int, goles_visit_int, partido_id)
                            cursor.execute(sql_update, params)
                            updated += 1

                            if estado_actualizado == 3 and estado_previo != 3:
                                win_id, lose_id = (None, None)
                                if goles_local_int > goles_visit_int:
                                    win_id, lose_id = equipo_local_id, equipo_visitante_id
                                elif goles_visit_int > goles_local_int:
                                    win_id, lose_id = equipo_visitante_id, equipo_local_id

                                if win_id and lose_id:
                                    cursor.execute(
                                        "UPDATE Equipo SET PartidosGanados = PartidosGanados + 1 WHERE Equipo_ID = ?",
                                        win_id)
                                    cursor.execute(
                                        "UPDATE Equipo SET PartidosPerdidos = PartidosPerdidos + 1 WHERE Equipo_ID = ?",
                                        lose_id)
                    else:

                        sql_check_fin = "SELECT 1 FROM Partido WHERE EquipoLocal_ID = ? AND EquipoVisitante_ID = ? AND Competicion_ID = ? AND Estado = 3"
                        cursor.execute(sql_check_fin, (equipo_local_id, equipo_visitante_id, competicion_id))

                        if not cursor.fetchone():
                            sql_ins = """
                                      INSERT INTO Partido (Estado, ResultadoLocal, ResultadoVisitante, Fecha, \
                                                           Competicion_ID, EquipoLocal_ID, EquipoVisitante_ID)
                                      VALUES (?, ?, ?, GETDATE(), ?, ?, ?) \
                                      """
                            params = (estado_actualizado, goles_local_int, goles_visit_int, competicion_id,
                                      equipo_local_id, equipo_visitante_id)
                            cursor.execute(sql_ins, params)
                            inserted += 1


                            if estado_actualizado == 3:
                                win_id, lose_id = (None, None)
                                if goles_local_int > goles_visit_int:
                                    win_id, lose_id = equipo_local_id, equipo_visitante_id
                                elif goles_visit_int > goles_local_int:
                                    win_id, lose_id = equipo_visitante_id, equipo_local_id

                                if win_id and lose_id:
                                    cursor.execute(
                                        "UPDATE Equipo SET PartidosGanados = PartidosGanados + 1 WHERE Equipo_ID = ?",
                                        win_id)
                                    cursor.execute(
                                        "UPDATE Equipo SET PartidosPerdidos = PartidosPerdidos + 1 WHERE Equipo_ID = ?",
                                        lose_id)

                    processed += 1

                except pyodbc.Error:
                    pass
                except Exception:
                    pass

            connection.commit()
            print(f"Proceso finalizado. Proc:{processed}, Ins:{inserted}, Upd:{updated}.")

    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except:
                pass
        print(f"Error General: {e}")
    finally:
        if connection: connection.close()

def estandarizar_estado_partido(tiempo_crudo):
    if not tiempo_crudo: return 0
    estado = str(tiempo_crudo).lower().strip()
    if estado == "final":
        return 3 #Finalizado
    elif estado[2:3] == ":":
        return 0 #Pendiente
    elif estado == "e":
        return 2 #Entretiempo
    else:
        return 1 #jugando

if __name__ == "__main__":
    datos = obtener_resultados()
    if datos:
        agregar_partido(datos)
    else:
        print("Finalizando: No se obtuvieron datos del scraper.")