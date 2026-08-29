# Load the .tflite model, run inference on the test set,
# compute accuracy for disease classification and severity
# classification separately, also train a single-modality
# image-only baseline model and compute its accuracy,
# print the accuracy delta between multimodal and baseline

import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical
from tensorflow.lite.python.interpreter import Interpreter


def _encode(labels, severities):
    disease_classes = sorted(set(labels))
    severity_classes = ["LOW", "MEDIUM", "HIGH"]
    disease_idx = {c: i for i, c in enumerate(disease_classes)}
    severity_idx = {c: i for i, c in enumerate(severity_classes)}
    y_disease = to_categorical([disease_idx[l] for l in labels], num_classes=len(disease_classes))
    y_severity = to_categorical([severity_idx[s] for s in severities], num_classes=3)
    return y_disease, y_severity, len(disease_classes)


def evaluate_tflite(model_path: str, data):
    interpreter = Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    images = data["images"].astype("float32") / 255.0
    weather = data["weather"].astype("float32")
    y_disease, y_severity, _ = _encode(data["labels"], data["severities"])
    _, X_img, _, X_w, _, yd, _, ys = train_test_split(
        images, weather, y_disease, y_severity, test_size=0.2, random_state=42
    )

    in_details = interpreter.get_input_details()
    img_in = next(d for d in in_details if d["shape"][-1] == 3)
    w_in = next(d for d in in_details if d["shape"][-1] == 4)
    out_details = interpreter.get_output_details()
    disease_out = max(out_details, key=lambda d: d["shape"][-1])

    disease_correct = severity_correct = 0
    for i in range(len(X_img)):
        interpreter.set_tensor(img_in["index"], np.expand_dims(X_img[i], 0).astype(img_in["dtype"]))
        interpreter.set_tensor(w_in["index"], np.expand_dims(X_w[i], 0).astype(w_in["dtype"]))
        interpreter.invoke()
        pred = np.argmax(interpreter.get_tensor(disease_out["index"]))
        sev_pred = np.argmax(interpreter.get_tensor(
            [d for d in out_details if d is not disease_out][0]["index"]
        ))
        disease_correct += int(pred == np.argmax(yd[i]))
        severity_correct += int(sev_pred == np.argmax(ys[i]))

    n = len(X_img)
    return disease_correct / n, severity_correct / n


def train_baseline(data):
    images = data["images"].astype("float32") / 255.0
    y_disease, _, n_classes = _encode(data["labels"], data["severities"])
    X_tr, X_te, y_tr, y_te = train_test_split(images, y_disease, test_size=0.2, random_state=42)

    inp = keras.Input(shape=(512, 512, 3))
    base = keras.applications.MobileNetV3Small(include_top=False, weights=None, input_shape=(512, 512, 3))(inp)
    x = layers.GlobalAveragePooling2D()(base)
    x = layers.Dense(256, activation="relu")(x)
    out = layers.Dense(n_classes, activation="softmax")(x)
    model = keras.Model(inp, out)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    model.fit(X_tr, y_tr, validation_data=(X_te, y_te), epochs=10, batch_size=16, verbose=0)
    _, acc = model.evaluate(X_te, y_te, verbose=0)
    return acc


def main(model_path: str = "./krushak.tflite", dataset_path: str = "./dataset.npz"):
    data = np.load(dataset_path, allow_pickle=True)
    disease_acc, severity_acc = evaluate_tflite(model_path, data)
    baseline_acc = train_baseline(data)
    print(f"Multimodal disease accuracy : {disease_acc:.4f}")
    print(f"Multimodal severity accuracy: {severity_acc:.4f}")
    print(f"Image-only baseline accuracy: {baseline_acc:.4f}")
    print(f"Delta (multimodal - baseline): {disease_acc - baseline_acc:+.4f}")


if __name__ == "__main__":
    main()
