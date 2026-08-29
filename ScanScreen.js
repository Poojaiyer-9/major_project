import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  Button,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Camera } from 'expo-camera';
import * as Location from 'expo-location';
import { detectDisease } from '../services/api';

const CROP_STAGES = ['seedling', 'vegetative', 'flowering'];

export default function ScanScreen({ navigation }) {
  const [hasPermission, setHasPermission] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cropStage, setCropStage] = useState('vegetative');
  const cameraRef = useRef(null);

  useEffect(() => {
    (async () => {
      const cameraStatus = await Camera.requestCameraPermissionsAsync();
      const locationStatus = await Location.requestForegroundPermissionsAsync();
      setHasPermission(
        cameraStatus.status === 'granted' && locationStatus.status === 'granted'
      );
    })();
  }, []);

  const handleCapture = async () => {
    try {
      setLoading(true);
      if (!cameraRef.current) {
        throw new Error('Camera not ready');
      }
      const photo = await cameraRef.current.takePictureAsync();
      const location = await Location.getCurrentPositionAsync({});
      const result = await detectDisease(
        photo.uri,
        location.coords.latitude,
        location.coords.longitude,
        cropStage,
        'kn'
      );
      navigation.navigate('Result', { result });
    } catch (err) {
      console.warn('Capture failed', err);
    } finally {
      setLoading(false);
    }
  };

  if (hasPermission === null) {
    return <ActivityIndicator style={{ flex: 1 }} />;
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text>Camera and location permissions are required to scan a leaf.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Camera ref={cameraRef} style={styles.camera} ratio="1:1" />
      <View style={styles.controls}>
        <Text style={styles.label}>Crop growth stage</Text>
        <Picker
          selectedValue={cropStage}
          onValueChange={setCropStage}
          style={styles.picker}
        >
          {CROP_STAGES.map((stage) => (
            <Picker.Item key={stage} label={stage} value={stage} />
          ))}
        </Picker>
        {loading ? (
          <ActivityIndicator size="large" />
        ) : (
          <Button title="Capture Leaf" onPress={handleCapture} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  camera: { flex: 1, width: Dimensions.get('window').width },
  controls: { padding: 16, backgroundColor: '#fff' },
  label: { fontSize: 14, color: '#374151', marginBottom: 4 },
  picker: { height: 50, marginBottom: 12 },
});
