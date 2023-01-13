'''
This scripts automates the checking of the file from a specific folder.  The original purpose of this script is to quickly check the student who seem to have done nothing for a pre-class and inclass

The usage of the script are as follows: 

- Arguments for zip file path
-p path_type : zip
-d the day of assignment format -0[0-9], 1[0-9], ...
-ass : type of the assignment

Running: 
python39 file_size.py -p zip -d 01 -ass ICA

python39 is an alias for python3.9. I have issues with loading nbconvert in python3.10 so I instead required this script to be run in python3.9

'''
import os
import sys
import re
import zipfile
import argparse
import subprocess
import pathlib

import nbconvert as nb
from nbconvert.exporters import PDFExporter, MarkdownExporter, NotebookExporter
from nbconvert.writers.files import FilesWriter

DIR_PATH = '/Users/lesiyonr/Desktop/SCHOOL_WORK/graduate_school/teaching/repos/cmse801/student_grades/{}'

# errors handling


class MissingFileDirError(Exception):

    def __init__(self, path):
        self.message = f'Double check if this path exists \n  {path}'
        super().__init__(self.message)


def get_files_size(path, file_ext):

    if not os.path.exists(path):
        raise MissingFileDirError(path)

    files = get_file_dir(path, file_ext)

    files_sizes = [
        (find_name_from_file(file.split("/")[-1]), get_file_size(file))
        for file in files]
    return files_sizes


def get_file_dir(path, file_ext):

    files_in_directory = list(filter(
        lambda x: x.endswith((file_ext, 'md', 'pdf')), os.listdir(path)))

    files_full_path = [f'{path}/{file}' for file in files_in_directory]
    return files_full_path


def get_file_size(file):
    return os.stat(file).st_size


def find_name_from_file(name):
    #print(re.findall(r'-([^-]+)(?:-|$)', file_path))
    return name.split("-")[2]


def loading_from_zipfile(path, path_type, day, ass):
    # renaming files

    files = filter(lambda x: x.endswith(path_type), os.listdir(path))
    old_new_names_dict = {re.sub(r'\s+', '_', file.replace(',', "")): file
                          for file in files}

    for k, v in old_new_names_dict.items():
        rename_file(v, k, path)

    # find the zip file for a specific day.
    zipfile_key = list(filter(
        lambda x:
        x.split('_')[0] == f'Day-{day}',
        old_new_names_dict.keys())
    )[0]

    # base file:
    day_zip_file = old_new_names_dict.get(zipfile_key)
    base_file_size = find_reference_file_size(path, day, assignment=ass)
    return extract_content_from_zip(
        path, base_file_size, day_zip_file, day)


def extract_content_from_zip(path, base_file_size, day_zip_file, day):
    student_files_size = []
    c = 0
    # get the filesize for each content in the zipfile.
    with zipfile.ZipFile(f'{path}/{day_zip_file}', 'r') as archive:

        for file in archive.infolist():
            try:
                file_type = pathlib.Path(file.filename).suffix
                if file_type == '.md' or '.pdf':
                    # save this file to someone loadly so I can access then.
                    pass
                student_files_size.append(file_summary(file, base_file_size))
            except Exception as e:
                pass
    return student_files_size


def file_summary(file, base_file_size):
    file_type = pathlib.Path(file.filename).suffix
    student_name = find_name_from_file(file.filename)
    file_size = file.file_size
    diff_size = file.file_size - base_file_size.get(file_type)
    return (student_name, file_size, diff_size, file_type)


def rename_file(old_name, new_name, path):
    '''
    Move the files to name of this format for consistency and downstream work. 
    Format: Day-01_file_name.ext
    '''
    shell_command = ["mv", f"{path}/{old_name}", f"{path}/{new_name}"]
    if old_name == new_name:
        return
    subprocess.run(shell_command)


def get_base_file_name(file):
    return pathlib.Path(file).stem


def find_reference_file_size(path, day, assignment):

    file_path = f'{path}/{assignment.lower()}_base'
    base_file = list(
        filter(
            lambda x: x.startswith(
                f'Day-{day}') and x.endswith(".ipynb"),
            os.listdir(file_path))
    )[0]

    base_file_name = get_base_file_name(base_file)
    base_file_path = f'{file_path}/{base_file}'
    base_file_size = {
        ".md": convert_notebook_exporter_format(
            base_file_path, base_file_name, MarkdownExporter),
        ".ipynb": get_file_size(base_file_path)
    }
    return base_file_size


def convert_notebook_exporter_format(file, file_name, exporter):
    output, resources = nb.exporters.export(
        exporter=exporter, nb=file)

    file_writer = FilesWriter()
    converted_file = file_writer.write(output, resources, file_name)

    return get_file_size(converted_file)


def command_line(argv):

    parser = argparse.ArgumentParser(
        description="Find the size of the file in a directory or a zip file",
        add_help=True,
    )
    parser.add_argument('-p', '--path_type')
    parser.add_argument('-d', '--day')
    parser.add_argument('-pn', '--path_name')
    parser.add_argument('-ext', '--extension', default=".ipynb")
    parser.add_argument('-ass', '--assign_type')

    return parser.parse_args()


def write_data_to_dest(dest, files_sizes):
    if files_sizes == []:
        # potentially through an error to double check on file_path.
        return
    with open(dest, 'w') as fp:
        for line in files_sizes:
            student, file_size, file_diff, file_type = line
            fp.write(f'{student}, {file_size}, {file_diff}, {file_type}' + "\n")


def main():
    # renaming .zip file with name spaces.
    args = command_line(sys.argv)

    dir_path = DIR_PATH.format(args.assign_type.upper())

    files_sizes = []
    if args.path_type == 'zip':
        files_sizes = loading_from_zipfile(dir_path, args.path_type, args.day,
                                           args.assign_type)
    else:
        files_sizes = get_files_size(dir_path, file_ext=args.extension)

    write_data_to_dest(f'Day_{args.day}_{args.assign_type}.txt', files_sizes)


if __name__ == "__main__":
    main()
