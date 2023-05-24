import os
import json
from utils import *

def get_path_dict(path,outpath):
    if path[-1] == '/':
        path = path[:-1]
    
    pass_id = os.listdir(path)[0].split('/')[-1].split('_')[0]
    folder_name = path.split('/')[-1]

    east_outpath = os.path.join(outpath,"east",folder_name)
    east_downsampled_outpath = os.path.join(outpath,"east_downsampled",folder_name)
    west_outpath = os.path.join(outpath,"west",folder_name)
    west_downsampled_outpath = os.path.join(outpath,"west_downsampled",folder_name)
    merged_outpath = os.path.join(outpath,"merged",folder_name)
    merged_downsampled_outpath = os.path.join(outpath,"merged_downsampled",folder_name)
    meta_data_outpath = os.path.join(outpath,"metadata",folder_name)

    os.makedirs(east_outpath,exist_ok=True)
    os.makedirs(east_downsampled_outpath,exist_ok=True)
    os.makedirs(west_outpath,exist_ok=True)
    os.makedirs(west_downsampled_outpath,exist_ok=True)
    os.makedirs(merged_outpath,exist_ok=True)
    os.makedirs(merged_downsampled_outpath,exist_ok=True)
    os.makedirs(meta_data_outpath,exist_ok=True)

    metadata_path = os.path.join(path,f"{pass_id}_metadata.json")
    west_png_path = os.path.join(path,f"{pass_id}__Top-heading-west_0_g.png")
    east_png_path = os.path.join(path,f"{pass_id}__Top-heading-east_0_g.png")
    west_ply_path = os.path.join(path,f"{pass_id}__Top-heading-west_0.ply")
    east_ply_path = os.path.join(path,f"{pass_id}__Top-heading-east_0.ply")

    east_tr_ply_path = os.path.join(east_outpath,f"{pass_id}__Top-heading-east.ply")
    west_tr_ply_path = os.path.join(west_outpath,f"{pass_id}__Top-heading-west.ply")
    east_tr_downsampled_ply_path = os.path.join(east_downsampled_outpath,f"{pass_id}__Top-heading-east.ply")
    west_tr_downsampled_ply_path = os.path.join(west_downsampled_outpath,f"{pass_id}__Top-heading-west.ply")

    updated_metadata_path = os.path.join(meta_data_outpath,f"{pass_id}_updated-metadata.json")
    merged_ply_path = os.path.join(merged_outpath,f"{pass_id}__Top-heading-merged.ply")
    merged_downsampled_ply_path = os.path.join(merged_downsampled_outpath,f"{pass_id}__Top-heading-merged.ply")

    path_dict = {}
    path_dict['metadata_path'] = metadata_path
    path_dict['west_png_path'] = west_png_path
    path_dict['east_png_path'] = east_png_path
    path_dict['west_ply_path'] = west_ply_path
    path_dict['east_ply_path'] = east_ply_path
    path_dict['merged_ply_path'] = merged_ply_path
    path_dict['merged_downsampled_ply_path'] = merged_downsampled_ply_path
    path_dict['updated_metadata_path'] = updated_metadata_path
    path_dict['pass_id'] = pass_id
    path_dict['folder_name'] = folder_name

    # separation
    path_dict['east_tr_ply_path'] = east_tr_ply_path
    path_dict['west_tr_ply_path'] = west_tr_ply_path
    path_dict['east_tr_downsampled_ply_path'] = east_tr_downsampled_ply_path
    path_dict['west_tr_downsampled_ply_path'] = west_tr_downsampled_ply_path
    

    return path_dict

def preprocess_single_pass(path,outpath,lid_path):

    lids = load_lids(lid_path)
    path_dict = get_path_dict(path,outpath)

    metadata = load_metadata_dict(path_dict['metadata_path'])
    start_point_gantry = (float(metadata['gantry_system_variable_metadata']['position x [m]']),float(metadata['gantry_system_variable_metadata']['position y [m]']),0)
    easting,northing = scanalyzer_to_utm(start_point_gantry[0],start_point_gantry[1])
    is_positive_dir = metadata['gantry_system_variable_metadata']['scanIsInPositiveDirection'] == "True"

    print(":: Metadata loaded successfully.")
    print(f":: Scan is in positive direction: {is_positive_dir}")
    print(f":: Scan start coordinate (Gantry): {start_point_gantry}")
    print(f":: Scan start coordinate (UTM-GPS): {easting},{northing}")

    if not os.path.exists(path_dict['merged_ply_path']):
        
        west_pcd = load_pcd(path_dict['west_ply_path'])
        east_pcd = load_pcd(path_dict['east_ply_path'])
        down_west_pcd = downsample_pcd(west_pcd)
        down_east_pcd = downsample_pcd(east_pcd)
        ew_pass_offset = 61.2552933403*(float(metadata['gantry_system_variable_metadata']['position z [m]'])) - 7.8968761675

        merged_pcd,merged_down_pcd,new_east,new_east_down = merge_east_west_ransac(east_pcd,west_pcd,down_east_pcd,down_west_pcd,down_east_pcd, ew_pass_offset)

        new_east = rotate_pcd(new_east,90,merged_down_pcd)
        new_west = rotate_pcd(west_pcd,90,merged_down_pcd)
        new_east_down = rotate_pcd(new_east_down,90,merged_down_pcd)
        new_west_down = rotate_pcd(down_west_pcd,90,merged_down_pcd)
        
        merged_down_pcd = rotate_pcd(merged_down_pcd,90)
        merged_pcd = rotate_pcd(merged_pcd,90)

        if metadata['gantry_system_variable_metadata']['scanIsInPositiveDirection'] == "False":
            merged_down_pcd = merged_down_pcd.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            merged_pcd = merged_pcd.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_east = new_east.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_west = new_west.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_east_down = new_east_down.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_west_down = new_west_down.translate([0,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
        else:
            
            dx = 135+0.845*(1083-float(metadata['gantry_system_variable_metadata']['position z [m]']))
            x_translation = 411.0301768990*(float(metadata['gantry_system_variable_metadata']['position z [m]']))-726.3787721123
            x_corrected = 23902.33376187-dx+x_translation
            
            merged_down_pcd = merged_down_pcd.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            merged_pcd = merged_pcd.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_east = new_east.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_west = new_west.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_east_down = new_east_down.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
            new_west_down = new_west_down.translate([x_corrected,(float(metadata['gantry_system_variable_metadata']['position x [m]'])-3.798989)/(8.904483-7.964989)*1000,0])
        
        boundaries = get_boundings_pcd(merged_down_pcd)
        print(":: Boundaries: ", boundaries)

        save_pcd(merged_down_pcd,path_dict['merged_downsampled_ply_path'])
        save_pcd(merged_pcd,path_dict['merged_ply_path'])
        save_pcd(new_east,path_dict['east_tr_ply_path'])
        save_pcd(new_west,path_dict['west_tr_ply_path'])
        save_pcd(new_east_down,path_dict['east_tr_downsampled_ply_path'])
        save_pcd(new_west_down,path_dict['west_tr_downsampled_ply_path'])
        
        
        

    else:
        merged_down_pcd = load_pcd(path_dict['merged_downsampled_ply_path'])
        boundaries = get_boundings_pcd(merged_down_pcd)
            
    processed_meta_dict = {}
    processed_meta_dict['folder_name'] = path_dict['folder_name']
    processed_meta_dict['pass_id'] = path_dict['pass_id']
    processed_meta_dict['boundaries'] = boundaries
    processed_meta_dict['gantry_start'] = {'x':start_point_gantry[0],'y':start_point_gantry[1]}
    processed_meta_dict['GPS_start'] = {'easting':easting,'northing':northing}
    processed_meta_dict['is_positive_dir'] = is_positive_dir
#     processed_meta_dict['height_offset'] = dx
#     processed_meta_dict['positive_direction_offset'] = 23902.33376187-dx

    possible_lids = get_possible_lid_pass((easting,northing),lids)
    if len(possible_lids)>0:
        processed_meta_dict['possible_lid'] = True
    else:
        processed_meta_dict['possible_lid'] = False

    with open(path_dict['updated_metadata_path'],'w') as f:
        json.dump(processed_meta_dict,f)
