from PIL import Image, ImageDraw
import openslide
import numpy as np
from arg_parser import ArgParser
from read_tiles_lmdb import LmdbReader

import matplotlib.pyplot as plt
from xml.dom import minidom
from shapely.geometry import Polygon


params = ArgParser().get_args()

LMDB_PATH = params.lmdbpath
LMDB_FILENAME = params.lmdbfilename
SLIDE_FULL_PATH = params.slide
IMG_SAVE_FULL_PATH = params.out
PRED_FILE = params.pred
XML_FILE = params.xml


slide = openslide.OpenSlide(SLIDE_FULL_PATH)
slide_pixel_width, slide_pixel_height = slide.dimensions

PIL_DIM_WANTED = (1200, 1200)
""" extract slide as PIL image 
RGB mode """
slide_pil_img = slide.get_thumbnail(PIL_DIM_WANTED)
""" real size (width, height) of png image """
PIL_EXTRACTED_DIM_X, PIL_EXTRACTED_DIM_Y = slide_pil_img.size
ZOOM_RATIO_X = slide_pixel_width/PIL_EXTRACTED_DIM_X
ZOOM_RATIO_Y = slide_pixel_height/PIL_EXTRACTED_DIM_Y
# input patch size for DNN pred script
patch_size = 100


def draw_heatmap_overlay(base_layer_img):
    """ Draw heatmap on color slide image or black-white image
    :arg
        -   base_layer_img: the layer draw the heatmap onto
    """
    lmdb_tile_file = LmdbReader(LMDB_PATH, LMDB_FILENAME)
    metas = lmdb_tile_file.get_meta_info()
    patch_on_slide_size = metas["patch_on_slide_size"]

    pred_list = []
    with open(PRED_FILE, 'r') as f:
        for line in f:
            parts = line.split(' ')
            x = int(parts[0])
            y = int(parts[1])
            score = float(parts[2])
            pred_list.append([x, y, score])

    for i in range(len(pred_list)):
        mid_point_x = int(pred_list[i][0])
        mid_point_y = int(pred_list[i][1])
        pixel_val = int(pred_list[i][2] * 255)
        offset = int((patch_on_slide_size-1)/2)
        # paste heat map on original color slide image
        if pixel_val > int(0.5*255):
            block_color = 255-pixel_val  # color: 100% pred val means black(0) and 0% is empty(255)

            new_block = Image.new(mode='RGB',
                                  size=(int(patch_on_slide_size/ZOOM_RATIO_X), int(patch_on_slide_size/ZOOM_RATIO_Y)),
                                  color=(block_color, block_color, block_color)
                                  )
            base_layer_img.paste(new_block, (int((mid_point_x-offset)/ZOOM_RATIO_X), int((mid_point_y-offset)/ZOOM_RATIO_Y)))

    return base_layer_img
    #slide_pil_img.show()


def parse_xml_points(xml_file):
    """ get xml regions(annotated tumor areas), and coordinates of each region
    :arg
    :returns
        - regions[points_of_region1[(x,y)], points_of_region2[(x,y)], ...]
        - region_labels [label_region1, label_region2, ...]
    """
    xml = minidom.parse(xml_file)
    # The first region marked is always the tumour delineation
    regions_ = xml.getElementsByTagName("Region")
    regions_points_list, region_labels_list = [], []
    for region in regions_:
        vertices = region.getElementsByTagName("Vertex")
        attribute = region.getElementsByTagName("Attribute")
        if len(attribute) > 0:
            r_label = attribute[0].attributes['Value'].value
        else:
            r_label = region.getAttribute('Text')
        region_labels_list.append(r_label)

        # Store x, y coordinates into a 2D array
        xy_coords = np.zeros((len(vertices), 2))

        for i, vertex in enumerate(vertices):
            xy_coords[i][0] = vertex.attributes['X'].value
            xy_coords[i][1] = vertex.attributes['Y'].value

        regions_points_list.append(xy_coords)
    return regions_points_list, region_labels_list


def draw_xml_roi(base_layer_img, image_type):
    """ Draw roi circle onto img
    :arg
        -   base_layer_img: the layer draw the roi onto
        -   image_type: 'slide' slide image as background, with black dots as heatmap
                        'bw': a white background img, with black dots as heatmap
    """
    regions_points_list = parse_xml_points(XML_FILE)
    fig1 = plt.figure(figsize=(14, 12))
    fig1.tight_layout()
    plt.axis('off')
    plt.imshow(base_layer_img)
    #plt.title(SLIDE_FULL_PATH.split('/')[-1])

    for region in regions_points_list:
        for sub_region in region:
            if len(sub_region) > 0:
                roi = Polygon(sub_region)
                print("Area of Region: ", roi.area)

                x, y = roi.exterior.xy  # (x,y) coordinates for plot figure
                # rescale to fit PIL image size
                x = [i/ZOOM_RATIO_X for i in x]
                y = [j/ZOOM_RATIO_Y for j in y]
                plt.plot(x, y, color='lime', linewidth=2.0)
    #plt.show()
    save_format = IMG_SAVE_FULL_PATH.split('.')[-1]
    save_name = IMG_SAVE_FULL_PATH.replace(save_format, '')
    color_mode = base_layer_img.mode
    fig1.savefig(save_name+image_type+'.'+save_format, bbox_inches='tight', pad_inches=0)


if __name__ == '__main__':
    color_slide_heatmap = draw_heatmap_overlay(base_layer_img=slide_pil_img)
    # draw black-white with roi map
    im_heatmap_bw = Image.new('RGB', (PIL_EXTRACTED_DIM_X, PIL_EXTRACTED_DIM_Y), (255, 255, 255))
    im_heatmap_bw = draw_heatmap_overlay(base_layer_img=im_heatmap_bw)

    if XML_FILE:
        draw_xml_roi(color_slide_heatmap, image_type='slide')
        draw_xml_roi(im_heatmap_bw, image_type='bw')

