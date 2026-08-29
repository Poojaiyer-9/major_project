# Convert the trained Keras model to TFLite format with
# INT8 post-training quantization using a representative
# dataset generator from the training set, save as
# krushak.tflite, print final model size in KB

import os

import numpy as np
import tensorflow as tf


def representative_dataset_gen(dataset_path: str = "./dataset.npz", num_samples: int = 200):
    data = np.load(dataset_path, allow_pickle=True)
    images = data["images"].astype("float32") / 255.0
    weather = data["weather"].astype("float32")
    idx = np.linspace(0, len(images) - 1, num_samples).astype(int)
    for i in idx:
        yield (
            np.expand_dims(images[i], axis=0),
            np.expand_dims(weather[i], axis=0),
        )


def convert_model(
    model_path: str = "./model.keras",
    dataset_path: str = "./dataset.npz",
    output_path: str = "./krushak.tflite",
):
    model = tf.keras.models.load_model(model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: representative_dataset_gen(dataset_path)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_model)
    print(f"Saved {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")


if __name__ == "__main__":
    convert_model()
