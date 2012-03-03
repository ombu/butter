from __future__ import with_statement
from fabric.operations import run
from fabric.api import task, env, cd, hide
from fabric.contrib import files
from time import gmtime, strftime
import os

@task
def log():
    """
    Tail a the deployment log of a host
    """
    print('+ Reading deployment log...')
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            out = run('cat DEPLOYMENTS')
            print(out)

def mark(parsed_ref):
    """
    Mark a deployment
    """
    from time import gmtime, strftime
    print('+ Logging deployment')
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            if not files.exists('DEPLOYMENTS'):
                print('+ No DEPLOYMENTS file found. Creating one.')
                run('touch DEPLOYMENTS');
            run('chmod u+w DEPLOYMENTS')
            date= strftime("%Y.%m.%d at %H:%M:%SUTC", gmtime())
            run('echo "%s by %s: %s" >> DEPLOYMENTS' % (date, os.getlogin(), parsed_ref))
            run('chmod u-w DEPLOYMENTS')
