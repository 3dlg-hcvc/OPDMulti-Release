import os
import glob
import json
import numpy as np
import pdb
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from functools import partial

data_dir = {"all": "/localhome/xsa55/Xiaohao/multiopd/scripts/mask2d/output/opdmulti_V3_processed"}
name_map_path = "/localhome/xsa55/Xiaohao/multiopd/scripts/mask2d/output/data_statistics/real_name_V3.json"
datasets = ['all']

TESTIDSPATH = '/localhome/xsa55/Xiaohao/multiopd/data_archive/MultiScan_dataset/scan_list/test_scanids.json'
VALIDSIDPATH = '/localhome/xsa55/Xiaohao/multiopd/data_archive/MultiScan_dataset/scan_list/val_scanids.json'
TRAINIDSPATH = '/localhome/xsa55/Xiaohao/multiopd/data_archive/MultiScan_dataset/scan_list/train_scanids.json'

if __name__ == "__main__":

    with open(name_map_path) as f:
        name_map = json.load(f)

    total_stat = {}

    test_scan_list = "/localhome/xsa55/Xiaohao/multiopd/scripts/mask2d/output/data_statistics/test_scan.json"
    val_scan_list = "/localhome/xsa55/Xiaohao/multiopd/scripts/mask2d/output/data_statistics/valid_scan.json"
    train_scan_list = "/localhome/xsa55/Xiaohao/multiopd/scripts/mask2d/output/data_statistics/train_scan.json"

    test_ids_file = open(test_scan_list)
    test_scans = json.load(test_ids_file)
    test_ids_file.close()

    valid_ids_file = open(val_scan_list)
    val_scans = json.load(valid_ids_file)
    valid_ids_file.close()

    train_ids_file = open(train_scan_list)
    train_scans = json.load(train_ids_file)
    train_ids_file.close()

    test_ids = []
    val_ids = []
    train_ids = []
    for dataset in datasets:

        current_object = {}
        current_object_number = 0
        current_scan_number = 0
        current_image_number = 0
        dirs = glob.glob(f"{data_dir[dataset]}")

        for dir in tqdm(dirs):
            # print(f"working on {dir}")
            model_name = dir.split('/')[-1]
            current_object[model_name] = glob.glob(f"{dir}/rgb/*")
            current_object_number += 1
            current_image_number += len(current_object[model_name])
            scan_ids = []
            problem_scan_ids = []
            for image in tqdm(current_object[model_name]):
                image_name = (image.split('/')[-1]).split('.')[0]
                scan_id = (image.split('/')[-1]).split('.')[0][:50]
                if not os.path.isfile(f"{dir}/annotation/{image_name}.json"):
                    print(f"No annotation: {image}")
                    continue
                if scan_id not in scan_ids:
                    current_scan_number += 1
                    scan_ids.append(scan_id)
                # Read the motion number
                with open(f"{dir}/annotation/{image_name}.json") as f:
                    anno = json.load(f)
                # Make it consistent with 2DMotion dataset
                extrinsic_matrix = np.reshape(
                    anno["extrinsics"], (4, 4), order="F").flatten(order="F")
                anno["extrinsics"] = list(extrinsic_matrix)
                with open(f"{dir}/annotation/{image_name}.json", 'w') as f:
                    json.dump(anno, f)

                motion_number = len(anno["articulation"])
                motion_ids = [anno["partId"] for anno in anno["articulation"]]
                mask_paths = glob.glob(f"{dir}/mask/{image_name}_*")

                if not motion_number == len(mask_paths):
                    print(f"Not consistent mask and motion {image}")
                # Rename the RGB
                model_name = image_name.rsplit('-', 1)[0].rsplit("_", 1)[0]
                if model_name.split('_')[0] != "scene":
                    continue
                try:
                    new_image_name = name_map[model_name] + \
                        '-' + image_name.rsplit('_', 1)[1]
                except:
                    pdb.set_trace()
                os.system(
                    f"mv {dir}/rgb/{image_name}.png {dir}/rgb/{new_image_name}.png")
                # Rename the depth
                os.system(
                    f"mv {dir}/depth/{image_name}_d.png {dir}/depth/{new_image_name}_d.png")
                # Rename the annotation
                os.system(
                    f"mv {dir}/annotation/{image_name}.json {dir}/annotation/{new_image_name}.json")
                # Rename all the masks
                for mask_path in mask_paths:
                    mask_name = (mask_path.split('/')[-1]).split('.')[0]
                    if int(mask_name.rsplit('_', 1)[1]) not in motion_ids and int(mask_name.rsplit('_', 1)[1]) != 0:
                        import pdb
                        pdb.set_trace()
                    new_mask_name = f"{new_image_name}_{mask_name.rsplit('_', 1)[1]}"
                    os.system(
                        f"mv {dir}/mask/{mask_name}.png {dir}/mask/{new_mask_name}.png")

                if scan_id[:14] in test_scans:
                    test_ids.append(new_image_name)
                elif scan_id[:14] in val_scans:
                    val_ids.append(new_image_name)
                elif scan_id[:14] in train_scans:
                    train_ids.append(new_image_name)

        total_stat[dataset] = current_object

        print(f"{dataset} Set -> Object Number {current_object_number}, Scan Number {current_scan_number}, Image Number {current_image_number}, Avg Images Per Object {current_image_number/current_object_number}, Avg Images Per Scan {current_image_number/current_scan_number}")

    val_ids_file = open(VALIDSIDPATH, 'w')
    json.dump(val_ids, val_ids_file)
    val_ids_file.close()

    test_ids_file = open(TESTIDSPATH, 'w')
    json.dump(test_ids, test_ids_file)
    test_ids_file.close()

    train_ids_file = open(TRAINIDSPATH, 'w')
    json.dump(train_ids, train_ids_file)
    train_ids_file.close()
