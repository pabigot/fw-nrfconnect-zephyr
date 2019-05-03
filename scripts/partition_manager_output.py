#!/usr/bin/env python3
#
# Copyright (c) 2019 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-BSD-5-Clause-Nordic


import argparse
import yaml
from os import path


def get_header_guard_start(filename):
    macro_name = filename.split('.h')[0]
    return '''/* File generated by %s, do not modify */
#ifndef %s_H__
#define %s_H__''' % (__file__, macro_name.upper(), macro_name.upper())


def get_header_guard_end(filename):
    return "#endif /* %s_H__ */" % filename.split('.h')[0].upper()


DEST_HEADER = 1
DEST_KCONFIG = 2

def get_config_lines(pm_config, head, split, dest):
    config_lines = list()

    def add_line(a, b):
        config_lines.append(head + "PM_" + a + split + b)

    partition_id = 0
    for name, partition in sorted(pm_config.items(), key=lambda key_value_tuple: key_value_tuple[1]['address']):
        add_line("%s_ADDRESS" % name.upper(), "0x%x" % partition['address'])
        add_line("%s_SIZE" % name.upper(), "0x%x" % partition['size'])
        add_line("%s_ID" % name.upper(), "%d" % partition_id)
        add_line("%s_NAME" % name.upper(), "%s" % name)
        add_line("%d_LABEL" % partition_id, "%s" % name.upper())
        if dest is DEST_HEADER:
            add_line("%s_DEV_NAME" % name.upper(), "\"NRF_FLASH_DRV_NAME\"")

        pm_config[name]['partition_id'] = partition_id
        partition_id += 1
    add_line("NUM", "%d" % partition_id)

    return config_lines


def write_config_lines_to_file(pm_config_file_path, config_lines):
    with open(pm_config_file_path, 'w') as out_file:
        out_file.write('\n'.join(config_lines))


def write_pm_config(pm_config, name, out_path):
    pm_config_file = path.basename(out_path)
    config_lines = get_config_lines(pm_config, "#define ", " ", DEST_HEADER)

    image_config_lines = list.copy(config_lines)
    image_config_lines.append("#define PM_ADDRESS 0x%x" % pm_config[name]['address'])
    image_config_lines.append("#define PM_SIZE 0x%x" % pm_config[name]['size'])
    image_config_lines.insert(0, get_header_guard_start(pm_config_file))
    image_config_lines.append(get_header_guard_end(pm_config_file))
    write_config_lines_to_file(out_path, image_config_lines)


def write_kconfig_file(pm_config, out_path):
    config_lines = get_config_lines(pm_config, "", "=", DEST_KCONFIG)
    write_config_lines_to_file(out_path, config_lines)


def parse_args():
    parser = argparse.ArgumentParser(
        description='''Creates files based on Partition Manager results.''',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("--input", required=True, type=str,
                        help="Path to the input .yml file.")

    parser.add_argument("--config-file", required=True, type=str,
                        help="Path to the output .config file.")

    parser.add_argument("--input-names", required=True, type=str, nargs="+",
                        help="List of names of image partitions.")

    parser.add_argument("--header-files", required=True, type=str, nargs='+',
                        help="Paths to the output header files files."
                             "These will be matched to the --input-names.")

    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.input, 'r') as f:
        pm_config = yaml.safe_load(f)

    write_kconfig_file(pm_config, args.config_file)

    for name, header_file in zip(args.input_names, args.header_files):
        write_pm_config(pm_config, name, header_file)


if __name__ == "__main__":
    main()
