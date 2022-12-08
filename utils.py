import numpy as np
import open3d as o3d
import copy
import json
import cv2
import csv
import multiprocessing

from pyproj import Proj,transform
proj_4326 = Proj(init='epsg:4326')
proj_2151 = Proj(init='epsg:2152')

# Point cloud operations

def load_pcd(path):
    pcd = o3d.io.read_point_cloud(path,format="ply")
    return pcd

def get_boundings_pcd(pcd):
    mins = np.min(np.array(pcd.points),axis=0)
    maxs = np.max(np.array(pcd.points),axis=0)

    return {"mins":list(mins),"maxs":list(maxs)}

def downsample_pcd(pcd,voxel_size=10):
    pcd_down = copy.deepcopy(pcd).voxel_down_sample(voxel_size)
    print(f":: Downsampling info: full-size: {pcd} down-sampled-size: {pcd_down}")
    return pcd_down

def rotate_pcd(pcd ,rotation_theta=90, center_pcd=None):

    theta = np.radians(rotation_theta)

    if center_pcd is not None:
        min_x, min_y, min_z = center_pcd.get_min_bound()
        max_x, max_y, max_z = center_pcd.get_max_bound()

        center_x = abs(max_x - min_x)/2
        center_y = abs(max_y - min_y)/2
        center_z = abs(max_z - min_z)/2
    else:
        min_x, min_y, min_z = pcd.get_min_bound()
        max_x, max_y, max_z = pcd.get_max_bound()

        center_x = abs(max_x - min_x)/2
        center_y = abs(max_y - min_y)/2
        center_z = abs(max_z - min_z)/2

    rotation_matrix = np.array([[np.cos(theta), -np.sin(theta), 0],
                [np.sin(theta), np.cos(theta), 0],
                [0, 0, 1]])

    rotated_pcd = pcd.rotate(rotation_matrix, center=[center_x, center_y, center_z])

    return rotated_pcd

def translate_pcd(pcd,x,y,z):
    transformed_pcd = copy.deepcopy(pcd).translate((x,y,z))
    return transformed_pcd

def merge_east_west_ransac(east,west,down_east,down_west):
    tr = execute_manual_location_based_RANSAC(down_east,down_west,400,coefs=[5,5,0.1,0.5])
    
    new_east_down = translate_pcd(down_east,tr[0],tr[1],tr[2])
    new_east = translate_pcd(east,tr[0],tr[1],tr[2])

    east_points_down = np.array(new_east_down.points)
    west_points_down = np.array(down_west.points)
    merged_down = o3d.geometry.PointCloud() 
    merged_down.points = o3d.utility.Vector3dVector(np.concatenate([east_points_down,west_points_down]))

    east_points = np.array(new_east.points)
    west_points = np.array(west.points)
    merged = o3d.geometry.PointCloud() 
    merged.points = o3d.utility.Vector3dVector(np.concatenate([east_points,west_points]))

    return merged,merged_down,new_east,new_east_down

def save_pcd(pcd,path):
    o3d.io.write_point_cloud(path, pcd)

# PNG Operations

def load_png(path,scale=0.2):
    img = cv2.imread(path,cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    img = cv2.normalize(img, None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1)
    img = cv2.resize(img,(int(img.shape[1]*scale),int(img.shape[0]*scale)))
    if len(img.shape) == 2 or img.shape[2]==1:
        img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)

    return img

def merge_png_files(west_png_path,east_png_path,west_boundaries,east_boundaries,metadata):
    
    img_e = load_png(east_png_path)
    img_w = load_png(west_png_path)
    
    img_e_corrected = rotate_flip_png(img_e,True,metadata)
    img_w_corrected = rotate_flip_png(img_w,False,metadata)

    T = abs(east_boundaries['mins'][1]-west_boundaries['mins'][1])/(east_boundaries['maxs'][1]-east_boundaries['mins'][1])
    
    merged_frame = np.zeros((img_w_corrected.shape[0],img_w_corrected.shape[1]+int(T*img_e_corrected.shape[1]),3))
    merged_frame[:,:img_w_corrected.shape[1],:] = img_w_corrected
    merged_frame[:,int(T*img_e_corrected.shape[1]):,:] = img_e_corrected
    merged_frame = cv2.normalize(merged_frame, None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1)

    merged_frame = cv2.rotate(merged_frame, cv2.ROTATE_90_CLOCKWISE)
    
    return merged_frame

def rotate_flip_png(png,east,metadata):
    scan_direction = str(metadata['sensor_variable_metadata']['current setting Scan direction (automatically set at runtime)'])
    if scan_direction == '0':
        if east:
            png = np.rot90(png, 1)
        else:
            png = np.rot90(png, 1)
            png = np.flipud(png)
    elif scan_direction == '1':
        if east:
            png = np.rot90(png, 3)
            png = np.flipud(png)
        else:
            png = np.rot90(png, 3)

    return png

def save_png(path,png):
    cv2.imwrite(path,png)

# Coordinate System conversions

def utm_to_latlon(easting, northing):
    lon, lat = transform(proj_2151,proj_4326,easting,northing)
    return lon,lat

def latlon_to_utm(lon,lat):
    easting,northing = transform(proj_4326,proj_2151,lon,lat)
    return easting,northing

def scanalyzer_to_utm(gantry_x, gantry_y):
    
    ay = 3659974.971; by = 1.0002; cy = 0.0078;
    ax = 409012.2032; bx = 0.009; cx = - 0.9986;

    utm_x = ax + (bx * gantry_x) + (cx * gantry_y)
    utm_y = ay + (by * gantry_x) + (cy * gantry_y)

    return utm_x, utm_y

# Metadata operations

def load_metadata_dict(path):
    
    with open(path) as f:
        meta = json.load(f)['lemnatec_measurement_metadata']

    return meta

# Lids Operations

def load_lids(path):
    lids = {}

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            
            p = [float(rows[1]),float(rows[2])]
            # p = utm.from_latlon(p[0],p[1])
            p = latlon_to_utm(p[1],p[0])
            lids[int(float(rows[0]))] = [p[0],p[1]]
    
    return lids

def get_possible_lid_pass(start_point,lids):
    
    possible_lids = []

    for l in lids:
        lid = lids[l]
        y_distance = abs(lid[1]-start_point[1])
        x_distance = abs(lid[0]-start_point[0])

        if y_distance <= 0.8:
            possible_lids.append([lid,x_distance,y_distance])

    return possible_lids

# RANSAC Operations

def ransac_transform_and_get_inliers(args):

    source_down_points = args[0]
    target_down_points = args[1]
    tr_x = args[2]
    tr_y = args[3]
    tr_z = args[4]
    voxel_size = args[5]

    source_down = o3d.geometry.PointCloud() 
    source_down.points = o3d.utility.Vector3dVector(source_down_points)

    target_down = o3d.geometry.PointCloud() 
    target_down.points = o3d.utility.Vector3dVector(target_down_points)
    
    target_tree = o3d.geometry.KDTreeFlann(target_down)

    translated_source = copy.deepcopy(source_down).translate((tr_x,tr_y, tr_z))
    translated_points = translated_source.points
    
    number_matched_points = 0
    
    mins = np.min(translated_points,axis=0)
    maxs = np.max(translated_points,axis=0)

    for point in translated_points:

        [k, idx, _] = target_tree.search_radius_vector_3d(point, voxel_size)
        if len(idx)>1:
            number_matched_points+=1

    return tr_x,tr_y,tr_z,number_matched_points

def execute_manual_location_based_RANSAC(source_down,target_down,num_samples,voxel_size=1,coefs=[2,1,1,1]):

    tr_mean = (0,0,0)
    tr_sigma = (voxel_size*coefs[0],voxel_size*coefs[1],voxel_size*coefs[2])

    coords_x=np.random.normal(tr_mean[0],tr_sigma[0],num_samples)
    coords_y=np.random.normal(tr_mean[1],tr_sigma[1],num_samples)
    coords_z=np.random.normal(tr_mean[2],tr_sigma[2],num_samples)

    args = []

    for i,x in enumerate(coords_x):
        y = coords_y[i]
        z = coords_z[i]
        args.append((np.asarray(source_down.points),np.asarray(target_down.points),x,y,0,voxel_size*coefs[3]))

    processes = multiprocessing.Pool(multiprocessing.cpu_count()-2)
    results = processes.map(ransac_transform_and_get_inliers,args)
    processes.close()

    best_x = 0
    best_y = 0
    best_z = 0
    best_n = -1

    for x,y,z,n in results:
        if n>best_n:
            best_n = n
            best_x = x
            best_y = y
            best_z = z

    return (best_x,best_y,best_z)





