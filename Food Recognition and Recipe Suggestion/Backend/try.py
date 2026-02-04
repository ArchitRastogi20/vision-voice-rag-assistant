from predict_image import get_predictions

# Define the images and checkpoint path
images = [
    './Datasets/test/bell pepper/Image_2.jpg'
]
checkpoint_path = 'Backend/checkpoint.pth'

# Get predictions
predictions = get_predictions(images, checkpoint=checkpoint_path, threshold=0.3)
print(predictions)