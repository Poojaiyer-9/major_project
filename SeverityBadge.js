import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const CONFIG = {
  LOW: { bg: '#16a34a', label: 'Low' },
  MEDIUM: { bg: '#ca8a04', label: 'Medium' },
  HIGH: { bg: '#dc2626', label: 'High' },
};

export default function SeverityBadge({ severity }) {
  const selected = CONFIG[severity] || CONFIG.LOW;

  return (
    <View style={[styles.badge, { backgroundColor: selected.bg }]}>
      <Text style={styles.text}>{selected.label} Severity</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    alignSelf: 'flex-start',
  },
  text: { color: '#fff', fontWeight: '700' },
});
