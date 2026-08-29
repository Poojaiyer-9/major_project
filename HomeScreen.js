import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';

export default function HomeScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Krushak Hithaishi</Text>
      <Text style={styles.subtitle}>Offline disease detection with nearby shop guidance.</Text>
      <Button title="Start Scan" onPress={() => navigation.navigate('Scan')} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 8 },
  subtitle: { fontSize: 16, textAlign: 'center', marginBottom: 20, color: '#4b5563' },
});
