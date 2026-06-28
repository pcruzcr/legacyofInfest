import os, sys
output_dir =  master_planning
def write_doc(filename, content):
    path = os.path.join(output_dir, filename)
    with open(path,  w, encoding=utf-8) as f:
        f.write(content)
