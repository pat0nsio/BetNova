import { Pressable, StyleSheet, Text, View } from 'react-native';

import { esEnVivo, type Match } from '../lib/api';

type Props = {
  match: Match;
  onPress?: () => void;
};

export default function MatchCard({ match, onPress }: Props) {
  const enVivo = esEnVivo(match.tiempo);
  const empezado = match.goles_local !== '-' || match.goles_visitante !== '-';

  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [styles.card, pressed && onPress ? styles.pressed : null]}>
      <View style={styles.teams}>
        <Text style={styles.team} numberOfLines={1}>
          {match.local}
        </Text>
        <Text style={styles.team} numberOfLines={1}>
          {match.visitante}
        </Text>
      </View>

      <View style={styles.scoreBox}>
        <Text style={styles.score}>{empezado ? match.goles_local : ''}</Text>
        <Text style={styles.score}>{empezado ? match.goles_visitante : ''}</Text>
      </View>

      <View style={styles.statusBox}>
        <View style={[styles.badge, enVivo ? styles.badgeLive : styles.badgeIdle]}>
          <Text style={[styles.badgeText, enVivo ? styles.badgeTextLive : null]}>
            {match.tiempo}
          </Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 12,
    marginHorizontal: 12,
    marginVertical: 4,
    gap: 10,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  pressed: { opacity: 0.6 },
  teams: { flex: 1, gap: 6 },
  team: { fontSize: 15, color: '#1a1a1a', fontWeight: '500' },
  scoreBox: { alignItems: 'center', gap: 6, minWidth: 24 },
  score: { fontSize: 15, fontWeight: '700', color: '#1a1a1a' },
  statusBox: { minWidth: 56, alignItems: 'flex-end' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  badgeIdle: { backgroundColor: '#eef0f2' },
  badgeLive: { backgroundColor: '#e8f7ee' },
  badgeText: { fontSize: 12, color: '#555', fontWeight: '600' },
  badgeTextLive: { color: '#1f9d55' },
});
