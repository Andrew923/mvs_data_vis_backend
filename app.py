import os
import sys

# The path of the current Python script.
_CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
_TOP_PATH     = os.path.join(_CURRENT_PATH, 'dsta_mvs')

if _TOP_PATH not in sys.path:
    sys.path.insert( 0, _TOP_PATH)
    for i, p in enumerate(sys.path):
        print(f'{i}: {p}')

from flask import Flask, jsonify, request
import base64
from flask_cors import CORS

from api.dataset_player import DatasetProxy

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3001", "https://mvs-data-vis.vercel.app"]}})

@app.route("/")
def home():
    return "<p>Hello!</p>"

#get the list of scenes
@app.route("/getscenes", methods=['GET'])
def get_directories():
    if request.method != 'GET': return jsonify(success=False)

    scenes = list()
    for folder in os.listdir(os.environ.get('directory')):
        if os.path.isdir(f"{os.environ.get('directory')}/{folder}"):
            scenes.append(folder)
    return jsonify(scenes=scenes, success=True)

#get list of poses
@app.route("/getposes/<scene>", methods=['GET'])
def get_poses(scene):
    if request.method != 'GET': return jsonify(success=False)
    if scene == "": return jsonify(poses=list(), success=True)

    poses = list()
    for folder in os.listdir(f"{os.environ.get('directory')}/{scene}"):
        if os.path.isdir(f"{os.environ.get('directory')}/{scene}/{folder}"):
            poses.append(folder)
    return jsonify(poses=poses, success=True)

#return images at directory with index
@app.route("/<scene>/<pose>/<index>", methods=['GET'])
def get_images(scene, pose, index="000000"):
    if request.method != 'GET': return jsonify(success=False)

    directory = f"{os.environ.get('directory')}/{scene}/{pose}"

    #extract minimum and maximum indices
    indices = os.listdir(f"{directory}/cam0")
    indices = [int(v.split('_')[0]) for v in indices if "Fisheye" in v]
    max_index, min_index = max(indices), min(indices)
    if int(index) > max_index or int(index) < min_index:
        return jsonify(success=False)

    #get images
    image_data = list()
    distance_data = list()
    for folder in os.listdir(directory):
        if not folder.startswith("cam"): continue

        for filename in os.listdir(f"{directory}/{folder}"):
            if filename.startswith(index) and "Distance" not in filename:
                with open(f"{directory}/{folder}/{filename}", 'rb') as f:
                    image_data.append(base64.b64encode(f.read()).decode('utf-8'))

    #get transformation matrices and camera model objects
    dataset_player = DatasetProxy(os.environ.get('CONFIG'), os.environ.get('directory'))
    transformations = dict()
    camera_frame = dataset_player.dataset.map_camera_frame
    cameras = [v for k, v in camera_frame.items() if 'cam' in k]
    for i in range(len(cameras)):
        for j in range(len(cameras)):
            if i != j:
                transformations[(cameras[i], cameras[j])] = dataset_player.dataset.frame_graph.query_transform(f0=cameras[i], f1=cameras[j])
    camera_models = dict([(k, v.__dict__) for k, v in dataset_player.dataset.map_camera_model_raw.items()]) #raw or not raw

    
    if len(image_data) == 0:
        return jsonify(success=False)
    else:
        return jsonify(image_data=image_data, 
                       distance_data=distance_data, 
                       transformations=transformations,
                       camera_models=camera_models,
                       success=True)

if __name__ == '__main__':
    app.run(port=3000)