from flask import Flask, jsonify
import os, base64

app = Flask(__name__)

@app.route("/")
def home():
    return "<p>Hello, World!</p>"

#get the list of options
@app.route("/getoptions")
def get_directories():
    folders = list()
    for folder in os.listdir(os.getcwd()):
        if os.path.isdir(folder) and folder != '.git':
            folders.append(folder)
    return jsonify(folders=folders)

#return images at directory with index
@app.route("/<directory>/<index>")
def get_images(directory="images", index="000000"):
    image_data = []
    for folder in os.listdir(directory):
        if not folder.startswith("cam"): continue
        for filename in os.listdir(f"{directory}/{folder}"):
            if filename.startswith(index) and "Distance" not in filename:
                with open(f"{directory}/{folder}/{filename}", 'rb') as f:
                    image_data.append(base64.b64encode(f.read()).decode('utf-8'))
    if len(image_data) == 0:
        return 'No images found'
    else:
        return jsonify(image_data=image_data)

#get minimum and maximum index in a directory
@app.route("/indices/<directory>")
def get_limits(directory):
    minIndex, maxIndex = float('inf'), 0
    for folder in os.listdir(directory):
        if not folder.startswith("cam"): continue
        for file in os.listdir(f"{directory}/{folder}"):
            if "Fisheye" in file:
                index = int(file.split('_')[0])
                minIndex = min(minIndex, index)
                maxIndex = max(maxIndex, index)
        break
    return jsonify(minIndex=minIndex, maxIndex=maxIndex)


if __name__ == '__main__':
    app.run()
