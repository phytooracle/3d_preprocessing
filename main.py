import argparse
import preprocess

def get_args():
    
    parser = argparse.ArgumentParser(
        description='Preprocesing 3D data. This includes downsampling, merging east and west using RANSAC and merging PNG files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i',
                        '--input',
                        help='Path to the directory that contains single pass raw data from the gantry. It should include the east and west ply files as well as the PNG images and the metadata json file.',
                        metavar='input',
                        type=str,
                        required=True)
    
    parser.add_argument('-o',
                        '--output',
                        help='Path to the preprocessing directory where the results for the given single pass will be saved. Within the preprocessing directory, 7 sub-directories will be created (if not exist) for east, west, merged and downsampled of them as well as the updated metadata.',
                        metavar='output',
                        type=str,
                        required=True)

    parser.add_argument('-l',
                        '--lids',
                        help='Path to the csv that contains the lid coordinates for this specific season.',
                        metavar='lids',
                        type=str,
                        required=True)

    return parser.parse_args()

def main():
    args = get_args()
    preprocess.preprocess_single_pass(args.input,args.output,args.lids)

main()