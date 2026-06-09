import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  SectionList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import MatchCard from '../components/MatchCard';
import { getLive, getResults, type Match } from '../lib/api';

type Filtro = 'todos' | 'vivo';

type Section = { title: string; data: Match[] };

function agruparPorLiga(matches: Match[]): Section[] {
  const grupos: Record<string, Match[]> = {};
  for (const m of matches) {
    (grupos[m.liga] ??= []).push(m);
  }
  return Object.entries(grupos).map(([title, data]) => ({ title, data }));
}

export default function HomeScreen() {
  const router = useRouter();
  const [filtro, setFiltro] = useState<Filtro>('todos');
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(
    async (f: Filtro, modo: 'inicial' | 'refresh' = 'inicial') => {
      modo === 'refresh' ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        const data = f === 'vivo' ? await getLive() : await getResults();
        setMatches(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Error desconocido');
        setMatches([]);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  useEffect(() => {
    cargar(filtro);
  }, [filtro, cargar]);

  const secciones = useMemo(() => agruparPorLiga(matches), [matches]);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>BetNova</Text>
          <Pressable
            style={styles.refreshBtn}
            onPress={() => cargar(filtro, 'refresh')}
            disabled={refreshing || loading}>
            <Text style={styles.refreshText}>{refreshing ? 'Actualizando…' : '↻ Actualizar'}</Text>
          </Pressable>
        </View>
        <View style={styles.tabs}>
          {(['todos', 'vivo'] as const).map((f) => (
            <Pressable
              key={f}
              onPress={() => setFiltro(f)}
              style={[styles.tab, filtro === f && styles.tabActive]}>
              <Text style={[styles.tabText, filtro === f && styles.tabTextActive]}>
                {f === 'todos' ? 'Todos' : 'En vivo'}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#1f9d55" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>No se pudieron cargar los partidos.</Text>
          <Text style={styles.errorDetail}>{error}</Text>
          <Pressable style={styles.retry} onPress={() => cargar(filtro)}>
            <Text style={styles.retryText}>Reintentar</Text>
          </Pressable>
        </View>
      ) : (
        <SectionList
          sections={secciones}
          keyExtractor={(item, i) => item.game_id ?? `${item.local}-${item.visitante}-${i}`}
          renderSectionHeader={({ section }) => (
            <Text style={styles.sectionHeader}>{section.title}</Text>
          )}
          renderItem={({ item }) => (
            <MatchCard
              match={item}
              onPress={
                item.game_id
                  ? () => router.push({ pathname: '/game/[id]', params: { id: item.game_id! } })
                  : undefined
              }
            />
          )}
          contentContainerStyle={matches.length === 0 ? styles.center : styles.listContent}
          ListEmptyComponent={
            <Text style={styles.emptyText}>
              {filtro === 'vivo' ? 'No hay partidos en vivo ahora.' : 'No hay partidos.'}
            </Text>
          }
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => cargar(filtro, 'refresh')}
              tintColor="#1f9d55"
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f6f8' },
  header: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 12, gap: 12 },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: 28, fontWeight: '800', color: '#111' },
  refreshBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, backgroundColor: '#e7e9ec' },
  refreshText: { fontSize: 13, fontWeight: '600', color: '#333' },
  tabs: { flexDirection: 'row', backgroundColor: '#e7e9ec', borderRadius: 10, padding: 3 },
  tab: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
  tabActive: { backgroundColor: '#fff' },
  tabText: { fontSize: 14, fontWeight: '600', color: '#666' },
  tabTextActive: { color: '#111' },
  center: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: 24, gap: 10 },
  listContent: { paddingBottom: 24 },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '700',
    color: '#777',
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 6,
  },
  emptyText: { fontSize: 15, color: '#888' },
  errorText: { fontSize: 16, fontWeight: '600', color: '#c0392b' },
  errorDetail: { fontSize: 13, color: '#888', textAlign: 'center' },
  retry: { marginTop: 6, backgroundColor: '#1f9d55', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },
});
