import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';

import { getGameDetail, type MatchDetail } from '../../lib/api';

export default function GameScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [detail, setDetail] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      setDetail(await getGameDetail(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1f9d55" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>No se pudo cargar el partido.</Text>
        <Text style={styles.errorDetail}>{error}</Text>
        <Pressable style={styles.retry} onPress={cargar}>
          <Text style={styles.retryText}>Reintentar</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.scoreboard}>
        <Text style={styles.team}>{detail?.local ?? '—'}</Text>
        <Text style={styles.vs}>vs</Text>
        <Text style={styles.team}>{detail?.visitante ?? '—'}</Text>
        {detail?.estado ? <Text style={styles.estado}>{detail.estado}</Text> : null}
      </View>

      <Text style={styles.sectionTitle}>Eventos</Text>
      {detail?.eventos?.length ? (
        detail.eventos.map((ev, i) => (
          <View key={i} style={styles.eventRow}>
            <Text style={styles.eventText}>{ev}</Text>
          </View>
        ))
      ) : (
        <Text style={styles.emptyText}>Sin eventos para mostrar.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f6f8' },
  content: { padding: 16, gap: 8 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, gap: 10, backgroundColor: '#f5f6f8' },
  scoreboard: { backgroundColor: '#fff', borderRadius: 14, padding: 20, alignItems: 'center', gap: 6, marginBottom: 12 },
  team: { fontSize: 20, fontWeight: '700', color: '#111', textAlign: 'center' },
  vs: { fontSize: 13, color: '#999', fontWeight: '600' },
  estado: { marginTop: 8, fontSize: 14, color: '#1f9d55', fontWeight: '600' },
  sectionTitle: { fontSize: 13, fontWeight: '700', color: '#777', textTransform: 'uppercase', marginTop: 4 },
  eventRow: { backgroundColor: '#fff', borderRadius: 10, paddingVertical: 10, paddingHorizontal: 14 },
  eventText: { fontSize: 14, color: '#333' },
  emptyText: { fontSize: 14, color: '#888' },
  errorText: { fontSize: 16, fontWeight: '600', color: '#c0392b' },
  errorDetail: { fontSize: 13, color: '#888', textAlign: 'center' },
  retry: { marginTop: 6, backgroundColor: '#1f9d55', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },
});
