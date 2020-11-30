import os, sys
import time
import subprocess
sys.path.append("./python_script")

from slide_viewer import WsiViewer

from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

IMG_PATH = "./static/wsi_png_files/"
SVS_SAVE_PATH = "./static/uploads/wsi_svs_files/"
XML_SAVE_PATH = "./static/uploads/wsi_xml_files/"
LMDB_PATCH_SAVE_PATH = '/mnt/ramdisk/extracted_patches/'
PRED_SAVE_PATH = "./static/pred_result/"
HEATMAP_SAVE_PATH = "./static/heatmaps/"

# just put all parameters (pass to html) here;
PARAMS = {"wsi_png_image": 'N/A',
        "uploaded_svs": 'N/A', "svs_upload_complete": False,
        "patch_extract_status": 'Not Yet', "patch_extract_time": 0,
        "pred_status": 'Not Yet', "pred_time": 0,
        "heatmap_greyscale_image": 'N/A'}

# all html pages are stored in template folder.
# this is the definition under FLASK framework.
@app.route("/")
def index():
    return render_template("main_page.html")


@app.route('/svs_uploader', methods=['POST'])
def upload_svs_file():
    """
    returns:
        wsi_image: the PNG of WSI
        uploaded_svs: the name of SVS file
        svs_upload_complete: progress indicator
    """
    svs_file = request.files['svsfile']
       
    if svs_file.filename != '':
        svs_file.save(SVS_SAVE_PATH + svs_file.filename)
        wsi_viewer = WsiViewer(svs_file.filename)
        wsi_viewer.show_slide()
        PARAMS["wsi_png_image"] = IMG_PATH + svs_file.filename + '.png'
        PARAMS["uploaded_svs"] = svs_file.filename
        PARAMS["svs_upload_complete"] = True

    # return to main page and pass params
    return render_template("main_page.html",
        wsi_png_image = PARAMS["wsi_png_image"],
        uploaded_svs = PARAMS["uploaded_svs"],
        svs_upload_complete = PARAMS["svs_upload_complete"])


@app.route('/xml_uploader', methods=['POST'])
def upload_xml_file():
    xml_file = request.files['xmlfile']
    if xml_file.filename != '':
        xml_file.save(XML_SAVE_PATH + xml_file.filename)

    return render_template("main_page.html",
        wsi_png_image = PARAMS["wsi_png_image"],
        uploaded_svs = PARAMS["uploaded_svs"],
        svs_upload_complete = PARAMS["svs_upload_complete"])


# cmd example:
# python -O patch_extraction.py -is "PATH to SVS file" -ix "xml" -o "/mnt/ramdisk/extracted_patches" -mag 20 -ps 100
@app.route('/patch_extractor', methods=['GET','POST'])
def patch_extraction():
    start = time.time()
    SVS_FILENAME = request.form['svs_filename']
    print("SVS filename: ", SVS_FILENAME)

    if SVS_FILENAME != "":
        # dont need to "conda activate ENV"; direct run python under a ENV;
        # execute cmd
        exec_status = subprocess.run(["/home/tom/anaconda3/envs/openslide/bin/python",
                        "-O", "./python_script/wsi_patch_extractor/patch_extraction.py",
                        "-is", SVS_SAVE_PATH + SVS_FILENAME,
                        "-ix", "xml",
                        "-o", LMDB_PATCH_SAVE_PATH,
                        "-mag", "20", "-ps", "100"])

    total_time = int( time.time()-start )
    PARAMS["patch_extract_time"] = total_time
    PARAMS["patch_extract_status"] = 'Patches Extracted!'
    print("Patch extract total time: ", total_time)
    
    return render_template("main_page.html",
        wsi_png_image = PARAMS["wsi_png_image"],
        uploaded_svs = PARAMS["uploaded_svs"], svs_upload_complete = PARAMS["svs_upload_complete"],
        patch_extract_status = PARAMS["patch_extract_status"], patch_extract_time = PARAMS["patch_extract_time"])


"""
Step3: DNN pred
"""
@app.route('/dnn_pred', methods=['GET','POST'])
def dnn_pred():
    start = time.time()
    SVS_FILENAME = request.form['svs_filename']

    if SVS_FILENAME != "":
        lmdb_tiles = LMDB_PATCH_SAVE_PATH + SVS_FILENAME
        # python pred_lmdb_input.py -ip /mnt/ramdisk/extracted_patches -if SVS_FILE -o ./outfile
        exec_status = subprocess.run(["/home/tom/anaconda3/envs/theano/bin/python",
                        "./python_script/pred_Theano_Model/pred_lmdb_input.py",
                        "-gpu", "0",  # specify gpu 0 for current test;
                        "-ip", "/mnt/ramdisk/extracted_patches",
                        "-if", SVS_FILENAME,
                        "-o", PRED_SAVE_PATH + SVS_FILENAME])

        PARAMS["pred_status"] = 'Model Prediction Completed!'

    total_time = int( time.time()-start )
    print("DNN pred total time: ", total_time)
    PARAMS["pred_time"] = total_time
    
    return render_template("main_page.html",
        wsi_png_image = PARAMS["wsi_png_image"],
        uploaded_svs = PARAMS["uploaded_svs"], svs_upload_complete = PARAMS["svs_upload_complete"],
        patch_extract_status = PARAMS["patch_extract_status"], patch_extract_time = PARAMS["patch_extract_time"],
        pred_status = PARAMS["pred_status"], pred_time = PARAMS["pred_time"])


"""
Step 4: Gen Heat Map
"""
@app.route('/gen_heatmap', methods=['GET','POST'])
def gen_heatmap():
    SVS_FILENAME = request.form['svs_filename']

    if SVS_FILENAME != "":
        exec_status = subprocess.run(["/home/tom/anaconda3/envs/openslide/bin/python",
                        "./python_script/gen_heatmap/heatmap_gen.py",
                        "-s", SVS_SAVE_PATH + SVS_FILENAME,
                        "-p", PRED_SAVE_PATH + SVS_FILENAME,
                        "-lp", LMDB_PATCH_SAVE_PATH,
                        "-lf", SVS_FILENAME,
                        "-x", XML_SAVE_PATH+SVS_FILENAME.split('.')[0]+".xml",
                        "-o", HEATMAP_SAVE_PATH + SVS_FILENAME + '.png'])

        PARAMS["wsi_png_image"] = HEATMAP_SAVE_PATH + SVS_FILENAME + '.slide' + '.png'
        PARAMS["heatmap_greyscale_image"] = HEATMAP_SAVE_PATH + SVS_FILENAME + '.bw' + '.png'

    return render_template("main_page.html",
        #wsi_png_image = PARAMS["wsi_png_image"],
        wsi_png_image = PARAMS["wsi_png_image"],
        uploaded_svs = PARAMS["uploaded_svs"], svs_upload_complete = PARAMS["svs_upload_complete"],
        patch_extract_status = PARAMS["patch_extract_status"], patch_extract_time = PARAMS["patch_extract_time"],
        pred_status = PARAMS["pred_status"], pred_time = PARAMS["pred_time"],
        heatmap_greyscale_image = PARAMS["heatmap_greyscale_image"])


if __name__ == "__main__":
    app.run(host='localhost')


