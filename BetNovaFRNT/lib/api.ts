const DEFAULT_HOST =
  typeof window !== 'undefined' && window.location?.hostname
    ? window.location.hostname
    : '127.0.0.1';

export const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ?? `http://${DEFAULT_HOST}:5000`;

export type Match = {
  liga: string;
  local: string;
  visitante: string;
  goles_local: string;
  goles_visitante: string;
  tiempo: string;
  game_id: string | null;
};

export type MatchDetail = {
  local: string | null;
  visitante: string | null;
  estado: string | null;
  eventos: string[];
};

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { error?: string } | null;
    throw new Error(body?.error ?? `Error HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const getResults = () => getJSON<Match[]>('/results');
export const getLive = () => getJSON<Match[]>('/live');
export const getResultsByDate = (fecha: string) => getJSON<Match[]>(`/results/${fecha}`);
export const getGameDetail = (gameId: string) => getJSON<MatchDetail>(`/game/${gameId}`);

/** True si el partido está en juego o en entretiempo (misma lógica que el backend). */
export function esEnVivo(tiempo: string): boolean {
  const t = tiempo?.trim().toLowerCase();
  if (!t || t === 'final' || t === 'n/a' || t === '-') return false;
  if (t === 'e') return true;
  if (/^\d{1,2}:\d{2}$/.test(t)) return false; // horario de inicio
  return /\d/.test(t); // minuto de juego
}
