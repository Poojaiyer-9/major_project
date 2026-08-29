import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, ActivityIndicator, StyleSheet } from 'react-native';
import * as Location from 'expo-location';
import { getNearbyShops } from '../services/api';
import ShopCard from '../components/ShopCard';

export default function ShopsScreen({ route }) {
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(true);
  const { medicineName } = route.params || {};

  useEffect(() => {
    (async () => {
      const location = await Location.getCurrentPositionAsync({});
      const data = await getNearbyShops(location.coords.latitude, location.coords.longitude, medicineName);
      setShops(data || []);
      setLoading(false);
    })();
  }, [medicineName]);

  if (loading) {
    return <ActivityIndicator style={{ flex: 1 }} />;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Nearby Shops</Text>
      <FlatList data={shops} keyExtractor={(item, index) => `${item.shop_name}-${index}`} renderItem={({ item }) => <ShopCard shop={item} />} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 12 },
});
