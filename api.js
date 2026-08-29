const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export async function detectDisease(imageUri, lat, lon, cropStage, language) {
  const formData = new FormData();
  formData.append('image', {
    uri: imageUri,
    name: 'leaf.jpg',
    type: 'image/jpeg',
  });
  formData.append('lat', String(lat));
  formData.append('lon', String(lon));
  formData.append('crop_stage', cropStage);
  formData.append('language', language);

  const response = await fetch(`${BASE_URL}/detect`, {
    method: 'POST',
    body: formData,
  });
  return response.json();
}

export async function getNearbyShops(lat, lon, medicineName) {
  const response = await fetch(`${BASE_URL}/shops/nearby`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat, lon, medicine_name: medicineName }),
  });
  return response.json();
}
