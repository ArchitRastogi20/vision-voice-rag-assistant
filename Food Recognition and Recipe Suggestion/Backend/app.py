from flask import Flask, request, jsonify, render_template
import os
import requests
from llm_recipe import  masterchef
from generate_recipes import llm_recipe

from PIL import Image
from pathvalidate import sanitize_filename
from images_with_groq import get_items

app = Flask(__name__,template_folder='../Frontend',static_url_path='', static_folder='../Frontend/static')


@app.route('/')
def index():
    return render_template('index.html') 


def is_valid_image(file):
    try:
        Image.open(file)
        return True
    except Exception as e:
        return False
    
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def truncate_filename(filename, max_length=15):
    # Split the filename into name and extension
    name, ext = filename.rsplit('.', 1)
    
    # Check if the filename length exceeds the maximum length
    if len(filename) > max_length:
        truncated_name = name[:max_length - len(ext) - 3] + '...' + ext
    else:
        truncated_name = filename
        
    return truncated_name

@app.route('/predict', methods=['POST'])
def predict():
    no_ext = None
    no_img = None
    not_img = None
    invalid_img_ext = None
    invalid_ext_paths = None
    invalid_img_paths = None
    # Extract images
    images = request.files.getlist('image')
    # Define a directory to save the uploaded images
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Process the images and cuisine list
    invalid_img_paths = []
    invalid_ext_paths = []
    uploaded_image_paths = []
    imd_dict = {}
    for image in images:
        if image.filename == '':
            continue
        truncated_filename = truncate_filename(image.filename)
        if not allowed_file(truncated_filename):
            invalid_ext_paths.append(truncated_filename)
            continue
            
        # Save the image to the upload directory
        filename = sanitize_filename(truncated_filename)
        image_path = os.path.join(upload_dir, filename)
        image.save(image_path)
        uploaded_image_paths.append("./" + image_path)
        # Check if the file is a valid image
        if not is_valid_image(image_path):
            os.remove(image_path)  # Remove the invalid image file
            del uploaded_image_paths[-1]
            invalid_img_paths.append(truncated_filename)
            
        
        imd_dict["./"+ image_path] = truncated_filename
    if len(invalid_ext_paths) >= 1 and len(invalid_img_paths)>=1:
        invalid_img_ext = {'invalid_img_ext' : f'Invalid file format for the files {invalid_ext_paths} and Invalid image files for the files {invalid_img_paths}'}
        if not uploaded_image_paths:
            return invalid_img_ext
    if invalid_ext_paths:
        no_ext = f'Invalid file format. Please upload images with .png, .jpg, or .jpeg extensions. Invalid file names {invalid_ext_paths}'
        if not uploaded_image_paths:
            no_ext = {'no_ext': f'Invalid file format. Please upload images with .png, .jpg, or .jpeg extensions. Invalid file names {invalid_ext_paths}'}
            return no_ext
    
    if invalid_img_paths:
        not_img = {'not_img': f'The uploaded file is not a valid image. Please crosscheck and upload a valid image. Invalid file names {invalid_img_paths}'}
        if not uploaded_image_paths:
            return {'not_img': not_img}


    if not uploaded_image_paths:
        no_img = {'no_img': 'No images uploaded.'}
        return no_img
    # Return the uploaded image paths and cuisine list
    
    # Extract cuisine list
    cuisine_list = request.form.getlist('cuisine')[0].split(',')

    # Get predictions
    print(uploaded_image_paths)
    flattened_list = []
    undetected = []
    for i in range(len(uploaded_image_paths)):
        items = get_items(uploaded_image_paths[i])
        if not items:
             undetected.append(imd_dict[uploaded_image_paths[i]])
        flattened_list.extend(items)

    if len(flattened_list) == 0:
        no_item = {
            'no_item' : f"Sorry I could not detect any food items from the picture provided by you , Please try with more clear pictures, Undetected images {undetected}"
        }
        if invalid_img_paths:
            response = {
            'no_item' : f"Sorry I could not detect any food items from the picture provided by you , Please try with more clear pictures, Undetected images {undetected}",
            'not_img' : not_img
        }
            return response
        return no_item
    num_recipes = max(len(cuisine_list),2)
    print(num_recipes,cuisine_list)
    recipes = llm_recipe(num_recipes,flattened_list,cuisine_list)
    #save_json_to_js(response)
    # Replace newline characters with HTML line breaks
    #result_html = result.replace('\n', '<br>')
    response_data = {
        'detected_items': flattened_list,
        'recipes':recipes,
        'empty_img' : undetected,
        'no_img' : no_img,
        'not_img' :not_img,
        'no_ext' :no_ext,
        'invalid_img_ext' : invalid_img_ext
    }     
    return response_data
@app.route('/feedback', methods=['POST'])
def feedback():
    query = request.form.get('feedback')
    cuisine = request.form.get('cus_feedback')
    result = request.form.get('res_feedback')
    item = request.form.get('item_feedback')
    feedback_response = masterchef(query,cuisine,result,item)
    feedback_html = feedback_response.replace('\n','<br>')
    feedback_html = feedback_response.replace('\n','<br>')
    return feedback_html

@app.route('/speak_recipe', methods=['POST'])
def speak_recipe():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        # Use the service name from docker-compose
        tts_url = "http://tts-service:8000/tts"
        response = requests.post(tts_url, data={'text': text})
        
        if response.status_code == 200:
            return response.content, 200, {'Content-Type': 'audio/wav'}
        else:
            return jsonify({'error': 'TTS service failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
