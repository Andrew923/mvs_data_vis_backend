from flask import Flask, jsonify, request
import os, base64
from flask_cors import CORS

from dsta_mvs.dsta_mvs.mvs_utils.image_io.image_read import read_compressed_float

app = Flask(__name__)
os.environ['port'] = '3000'
os.environ['directory'] = 'images'
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
            if filename.startswith(index):
                if "Distance" in filename:
                    arr = read_compressed_float(f"{directory}/{folder}/{filename}")
                    distance_data.append(arr.tolist())
                else:
                    with open(f"{directory}/{folder}/{filename}", 'rb') as f:
                        image_data.append(base64.b64encode(f.read()).decode('utf-8'))
    if len(image_data) == 0:
        return jsonify(success=False)
    else:
        return jsonify(image_data=image_data, distance_data=distance_data, success=True)

if __name__ == '__main__':
    app.run(port=int(os.environ.get('port')))