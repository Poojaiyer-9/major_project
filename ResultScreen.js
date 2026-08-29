import React from 'react';
import { View, Text, Button, Image, StyleSheet } from 'react-native';
import { Audio } from 'expo-av';
import SeverityBadge from '../components/SeverityBadge';

export default function ResultScreen({ route, navigation }) {
  const { result } = route.params || {};

  const playVoice = async () => {
    if (!result?.voice_file_url) return;
    const sound = new Audio.Sound();
    await sound.loadAsync({ uri: result.voice_file_url });
    await sound.playAsync();
  };

  const displayName = result?.disease_display || result?.disease_name || 'No result';
  const medicineName = result?.treatment?.medicine_name;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{displayName}</Text>
      <Text>Confidence: {(result?.confidence * 100 || 0).toFixed(1)}%</Text>
      <SeverityBadge severity={result?.severity || 'LOW'} />
      <Text style={styles.advisory}>{result?.advisory_translated || ''}</Text>
      {result?.heatmap_base64 ? <Image source={{ uri: `data:image/jpeg;base64,${result.heatmap_base64}` }} style={styles.image} /> : null}
      <Button title="Play Voice" onPress={playVoice} />
      <Button title="Find Nearby Shops" onPress={() => navigation.navigate('Shops', { medicineName })} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 10 },
  title: { fontSize: 22, fontWeight: '700' },
  advisory: { marginTop: 8, color: '#374151' },
  image: { width: '100%', height: 220, marginVertical: 12 },
});
