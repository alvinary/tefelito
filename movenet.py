import tensorflow as tf
import tensorflow_hub as hub


model = hub.load("https://tfhub.dev/google/movenet/singlepose/thunder/4")
movenet = model.signatures['serving_default']

def read_frame(path):
    # Load the input image.
    image_path = path
    image = tf.io.read_file(image_path)
    image = tf.compat.v1.image.decode_bmp(image)
    image = tf.expand_dims(image, axis=0)
    
    # Resize and pad the image to keep the aspect ratio and fit the expected size.
    image = tf.cast(tf.image.resize_with_pad(image, 256, 256), dtype=tf.int32)

    # Run model inference.
    outputs = movenet(image)
    # Output is a [1, 1, 17, 3] tensor.
    keypoints = outputs['output_0']

    return keypoints[0][0]
