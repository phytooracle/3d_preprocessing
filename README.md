# 3d_preprocessing
This script preprocesses 3D point cloud data. It includes merging west and east and aligning north and south using RANSAC and finding passes that might contain lids. It paints the ply files and prepares them for manual selection of the lids in later processing steps.

## Inputs
Point clouds and metadata are required inputs.

## Outputs
Subdirectories containing preprocessed point cloud data.

## Arguments and Flags

* **Required Arguments:**
    * **File path to the point cloud data:** '-i', '--input'   
    * **Output directory for the results:** '-o', '--output'
    * **Lid containing the ground control point (GCP) coordinates:** '-l' '--lids'
    
## Lids file
The "lids" file contains the geocoordinate of each ground control point (GCP). The columns represent: GCP number, latitude, and longitude. These files can be found at: /iplant/home/shared/phytooracle/<season name>/level_0/necessary_files/gcp_season_<season number>_bucket.txt. Below is an example of the file:

```
128,33.0746228516618,-111.975006871447
129,33.0746213831943,-111.974952432095
131,33.0745976320083,-111.974898496887
132,33.0745997719148,-111.974843990219
```
