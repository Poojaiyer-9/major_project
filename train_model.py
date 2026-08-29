# Build a multimodal fusion Keras model: MobileNetV3Small
# branch for 512x512x3 image input producing 576-dim features,
# separate Dense(64) branch for 4-dim weather vector input,
# concatenate both branches, Dense(256) with dropout 0.3,
# two output heads: 38-class softmax for disease,
# 3-class softmax for severity. Compile with Adam optimizer
# and categorical crossentropy loss for both outputs.
# Train for 20 epochs with early stopping on val_loss

import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical


def build_model(num_disease_classes: int = 38, num_severity_classes: int = 3):
    image_input = keras.Input(shape=(512, 512, 3), name="image")
    weather_input = keras.Input(shape=(4,), name="weather")

    base_model = keras.applications.MobileNetV3Small(
        include_top=False,
        input_shape=(512, 512, 3),
        weights=None,
    )
    image_features = base_model(image_input)
    image_features = layers.GlobalAveragePooling2D()(image_features)
    image_features = layers.Dense(64, activation="relu")(image_features)

    weather_features = layers.Dense(64, activation="relu")(weather_input)
    merged = layers.Concatenate()([image_features, weather_features])
    merged = layers.Dense(256, activation="relu")(merged)
    merged = layers.Dropout(0.3)(merged)

    disease_output = layers.Dense(num_disease_classes, activation="softmax", name="disease")(merged)
    severity_output = layers.Dense(num_severity_classes, activation="softmax", name="severity")(merged)

    model = keras.Model(inputs=[image_input, weather_input], outputs=[disease_output, severity_output])
    model.compile(
        optimizer="adam",
        loss={"disease": "categorical_crossentropy", "severity": "categorical_crossentropy"},
        metrics={"disease": "accuracy", "severity": "accuracy"},
    )
    return model


def _encode(labels, severities):
    disease_classes = sorted(set(labels))
    severity_classes = ["LOW", "MEDIUM", "HIGH"]
    disease_idx = {c: i for i, c in enumerate(disease_classes)}
    severity_idx = {c: i for i, c in enumerate(severity_classes)}
    y_disease = to_categorical([disease_idx[l] for l in labels], num_classes=len(disease_classes))
    y_severity = to_categorical([severity_idx[s] for s in severities], num_classes=3)
    return y_disease, y_severity, len(disease_classes)


def train(dataset_path: str = "./dataset.npz", model_out: str = "./model.keras"):
    data = np.load(dataset_path, allow_pickle=True)
    images = data["images"].astype("float32") / 255.0
    weather = data["weather"].astype("float32")
    y_disease, y_severity, n_classes = _encode(data["labels"], data["severities"])

    (
        X_img_tr, X_img_te, X_w_tr, X_w_te, yd_tr, yd_te, ys_tr, ys_te,
    ) = train_test_split(
        images, weather, y_disease, y_severity, test_size=0.2, random_state=42
    )
    X_img_tr, X_img_val, X_w_tr, X_w_val, yd_tr, yd_val, ys_tr, ys_val = train_test_split(
        X_img_tr, X_w_tr, yd_tr, ys_tr, test_size=0.125, random_state=42
    )

    model = build_model(num_disease_classes=n_classes)
    model.fit(
        {"image": X_img_tr, "weather": X_w_tr},
        {"disease": yd_tr, "severity": ys_tr},
        validation_data=({"image": X_img_val, "weather": X_w_val}, {"disease": yd_val, "severity": ys_val}),
        epochs=20,
        batch_size=16,
        callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True)],
    )
    model.save(model_out)
    print(f"Saved trained model to {model_out} ({n_classes} disease classes)")


if __name__ == "__main__":
    train()
