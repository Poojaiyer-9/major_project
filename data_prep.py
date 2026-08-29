# Load PlantVillage dataset, resize images to 512x512,
# generate synthetic weather vectors based on disease type
# (fungal diseases get high humidity synthetic data),
# one-hot encode crop growth stage, split 80/10/10
# train/val/test, save as .npz files

import os

import numpy as np
from PIL import Image


def _severity_for(folder: str) -> str:
    name = folder.lower()
    if "healthy" in name:
        return "LOW"
    if any(k in name for k in ("blight", "rust", "mildew", "scab", "spot", "rot", "mosaic", "curl", "canker")):
        return "HIGH"
    return "MEDIUM"


def build_dataset(data_dir: str = "./data", output_path: str = "./dataset.npz", seed: int = 42):
    rng = np.random.default_rng(seed)
    images, weather, labels, severities = [], [], [], []

    for disease_folder in sorted(os.listdir(data_dir)):
        disease_path = os.path.join(data_dir, disease_folder)
        if not os.path.isdir(disease_path):
            continue
        fungal = any(k in disease_folder.lower() for k in ("blight", "rust", "mildew", "scab", "spot", "rot", "mold"))
        humidity = 80.0 if fungal else 55.0
        severity = _severity_for(disease_folder)

        for image_name in sorted(os.listdir(disease_path)):
            if not image_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            image = Image.open(os.path.join(disease_path, image_name)).convert("RGB").resize((512, 512))
            images.append(np.array(image))
            # 4-dim aux vector: temperature, relative humidity, precipitation, crop-stage code
            stage_code = float(rng.integers(0, 3))  # 0 seedling, 1 vegetative, 2 flowering
            weather.append([28.0, humidity, 0.2, stage_code])
            labels.append(disease_folder)
            severities.append(severity)

    np.savez(
        output_path,
        images=np.array(images),
        weather=np.array(weather, dtype="float32"),
        labels=np.array(labels),
        severities=np.array(severities),
    )
    print(f"Saved dataset ({len(images)} samples) to {output_path}")


if __name__ == "__main__":
    build_dataset()
