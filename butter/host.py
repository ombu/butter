from fabric.operations import run
from fabric.contrib import files

def pre_clean(build_path):
    if files.exists(build_path):
        print('+ Found the same revision already deployed. Cleaning up')
        run('rm -rf %s' % build_path)
