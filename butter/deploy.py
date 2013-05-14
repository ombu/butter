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

@task
def clean(age=15):
    """
    Clean a `path` from files older than `age` days
    """
    with hide('running', 'stdout'):
        with cd('%s/changesets' % env.host_site_path):
            # count how many we'll delete
            count = run("""find . -maxdepth 1 -type d -mtime +%s ! -iname '\.'| wc -l""" %
                    age)
            # delete
            if count != '0':
                print('+ Removing %s deployments older than %s days' % (count, age))
                run("""find . -maxdepth 1 -type d -mtime +%s ! -iname '\.' -print0 \
                        | xargs -0 rm -rf""" % age)
