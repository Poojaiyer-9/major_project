import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function formatVerified(dateStr) {
  if (!dateStr) return 'Not verified';
  const [year, month] = dateStr.split('-');
  if (!year || !month) return dateStr;
  return `Verified: ${MONTHS[parseInt(month, 10) - 1]} ${year}`;
}

export default function ShopCard({ shop }) {
  const distance = typeof shop.distance_km === 'number' ? shop.distance_km.toFixed(1) : shop.distance_km;
  return (
    <View style={styles.card}>
      <Text style={styles.name}>{shop.shop_name}</Text>
      <Text style={styles.distance}>{distance} km away</Text>
      <Text style={styles.muted}>{shop.address}</Text>
      <Text style={styles.muted}>{formatVerified(shop.last_verified_date)}</Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => Linking.openURL(`tel:${shop.phone_number}`)}
      >
        <Text style={styles.buttonText}>Call {shop.phone_number}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  name: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  distance: { fontSize: 14, fontWeight: '600', color: '#16a34a', marginBottom: 2 },
  muted: { fontSize: 13, color: '#6b7280', marginBottom: 2 },
  button: {
    marginTop: 8,
    alignSelf: 'flex-start',
    backgroundColor: '#16a34a',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  buttonText: { color: '#fff', fontWeight: '600' },
});
