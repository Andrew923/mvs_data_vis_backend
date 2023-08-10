import os
import sys

# The path of the current Python script.
_CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
_TOP_PATH     = os.path.join(_CURRENT_PATH, 'dsta_mvs_lightning')

if _TOP_PATH not in sys.path:
    sys.path.insert( 0, _TOP_PATH)
    sys.path.insert( 1, os.path.join(_CURRENT_PATH, 'dsta_mvs'))

from flask import Flask, jsonify, request, render_template, send_from_directory
import base64, shutil
from flask_cors import CORS

from api.dataset_player import DatasetProxy
dataset_player = None

#search in data folder
if os.listdir('mvs_data_vis_backend/data'):
    os.environ['directory'] = 'mvs_data_vis_backend/data'
    for file in os.listdir('mvs_data_vis_backend/data'):
        if 'conf' in file: os.environ['CONFIG'] = f'mvs_data_vis_backend/data/{file}'

if None not in [os.environ.get('CONFIG'), os.environ.get('directory')]:
    dataset_player = DatasetProxy(os.environ.get('CONFIG'), os.environ.get('directory'))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [r"http://localhost:\d+", "https://mvs-data-vis.vercel.app"]}})

#STATIC SITE STUFF, maybe retry later
# app = Flask(__name__, static_folder='build', template_folder='build', static_url_path='')
# @app.route("/", methods=['GET'])
# def index():
#     return render_template('index.html')
# @app.route("/static/<folder>/<file>", methods=['GET'])
# def css(folder, file):
#     return send_from_directory(os.getcwd() + '/build/static/', folder + '/' + file)

#SSL certification stuff
@app.route("/.well-known/pki-validation/<file>", methods=['GET'])
def ssl_cert(file):
    return send_from_directory(os.getcwd(), file, as_attachment=True)

@app.route("/", methods=['GET'])
def home():
    return "<h1>Hello!</h1>"

@app.route("/upload", methods=['GET', 'PUT'])
def upload():
    global dataset_player
    if request.method == 'GET': return jsonify(success=(dataset_player != None))
    
    if request.method != 'PUT': return jsonify(success=False)

    #PUT dataset
    print("Uploading dataset ...")
    target = os.path.join(os.getcwd(), 'dataset')
    if os.path.isdir(target): shutil.rmtree(target)
    os.mkdir(target)

    for file in request.files.getlist('files[]'):
        filename = os.path.join(target, file.filename)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        file.save(filename)

    for file in os.listdir(target):
        if "conf" in file and ".py" in file:
            os.rename(os.path.join(target, file), os.path.join(os.getcwd(), file))
            dataset_player = DatasetProxy(f'./{file}', './dataset')
            os.environ['CONFIG'] = f'./{file}'
            break
    os.environ['directory'] = './dataset'
    print("Dataset uploaded!")
    return jsonify(success=(dataset_player != None))

@app.route("/clear", methods=['GET'])
def clear():
    global dataset_player
    if request.method != 'GET': return jsonify(success=False)
    dataset_player = None
    return jsonify(success=True)

#get the list of scenes
@app.route("/getscenes", methods=['GET'])
def get_directories():
    global dataset_player
    if request.method != 'GET': return jsonify(success=False)
    if dataset_player == None: return jsonify(scenes=list(), success=True)

    scenes = list()
    for folder in os.listdir(os.environ.get('directory')):
        if os.path.isdir(f"{os.environ.get('directory')}/{folder}"):
            scenes.append(folder)
    return jsonify(scenes=scenes, success=True)

#get list of poses
@app.route("/getposes/<scene>", methods=['GET'])
def get_poses(scene):
    global dataset_player
    if request.method != 'GET': return jsonify(success=False)
    if scene == "" or dataset_player == None: return jsonify(poses=list(), success=True)

    poses = list()
    for folder in os.listdir(f"{os.environ.get('directory')}/{scene}"):
        if os.path.isdir(f"{os.environ.get('directory')}/{scene}/{folder}"):
            poses.append(folder)
    return jsonify(poses=poses, success=True)

#return images at directory with index
@app.route("/<scene>/<pose>/<index>", methods=['GET'])
def get_images(scene, pose, index="000000"):
    global dataset_player
    if request.method != 'GET' or dataset_player == None: return jsonify(success=False)

    directory = f"{os.environ.get('directory')}/{scene}/{pose}"

    #extract minimum and maximum indices
    indices = os.listdir(f"{directory}/cam0")
    indices = [int(v.split('_')[0]) for v in indices if "Fisheye" in v]
    max_index, min_index = max(indices), min(indices)
    if int(index) > max_index or int(index) < min_index:
        return jsonify(success=False)

    #get images
    image_data = dict()
    distance_data = list()
    for folder in os.listdir(directory):
        if not folder.startswith("cam"): continue

        for filename in os.listdir(f"{directory}/{folder}"):
            if filename.startswith(index) and "Distance" not in filename:
                with open(f"{directory}/{folder}/{filename}", 'rb') as f:
                    image_data[folder] = base64.b64encode(f.read()).decode('utf-8')

    if len(image_data) == 0:
        return jsonify(success=False)
    else:
        return jsonify(image_data=image_data, 
                       distance_data=distance_data, 
                       success=True)

#get transformation matrices
@app.route("/transformations", methods=['GET'])
def get_transformations():
    global dataset_player
    if request.method != 'GET' or dataset_player == None: return jsonify(success=False)

    transformations = dict()
    camera_frame = dataset_player.dataset.map_camera_frame
    cameras = {k: v for k, v in camera_frame.items() if 'cam' in k}
    for i in cameras.keys():
        for j in cameras.keys():
            if i != j:
                matrix = dataset_player.dataset.frame_graph.query_transform(f0=cameras[i], f1=cameras[j])
                transformations[f"{i}-{j}"] = matrix.tolist()
    if len(transformations) == 0:
        return jsonify(success=False)
    else:
        return jsonify(transformations=transformations,
                       success=True)
    
#get camera models
@app.route("/cameras", methods=['GET'])
def get_cameras():
    global dataset_player
    if request.method != 'GET' or dataset_player == None: return jsonify(success=False)

    camera_models = dict()
    for cam, fields in dataset_player.dataset.map_camera_model_raw.items():
        new_fields = {k: v for k, v in fields.__dict__.items() if k in ['name', 'fx', 'fy', 'cx', 'cy', 'fov_degree', 'fov_rad']}
        camera_models[cam] = new_fields
    if len(camera_models) == 0:
        return jsonify(success=False)
    else:
        return jsonify(camera_models=camera_models,
                       success=True)

#get distance
@app.route("/distances/<scene>/<pose>/<index>", methods=['GET'])
def get_distance(scene, pose, index):
    global dataset_player
    if request.method != 'GET' or dataset_player == None: return jsonify(success=False)

    camera_frame = dataset_player.dataset.map_camera_frame
    cameras = [k for k, _ in camera_frame.items() if 'cam' in k]
    distances = dict()
    for cam in cameras:
        filenames = dataset_player.dataset.filenames[f'{cam}_dist_fisheye']
        i = filenames.index(f'{scene}/{pose}/{cam}/{index}_FisheyeDistance.png') #hardcoded filename format
        
        distances[cam] = dataset_player.dataset[i]['inv_dist_idx'].tolist()
    return jsonify(distances=distances, bf=dataset_player.dataset.dist_lab_tab.bf,
                success=True)

if __name__ == '__main__':
    app.run(port=49153)