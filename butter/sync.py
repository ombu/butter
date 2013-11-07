from fabric.api import task, env, execute, settings
from fabric.operations import run, local
from fabric.utils import abort
from copy import copy

@task
def files(dst='local'):
    """
    Syncs files from the environment's S3 bucket to `dst` env.files_path.
    """
    if dst == 'production':
        abort('Cannot sync to production.')
    execute(dst)
    dst_env = copy(env)
    if not 'files_path' in dst_env:
        abort('`files_path` not found in dst env.')
    if dst == 'local':
        # Ensure drupal.sync works anywhere in project structure by getting the
        # directory that the fabfile is in (project root).
        import os
        dst_files = os.path.dirname(env.real_fabfile) + '/' + dst_env.files_path
        local('aws --region=us-west-2 s3 sync %s %s' % (env.s3_bucket, dst_files));
    else:
        with settings(host_string=dst_env.hosts[0]):
            dst_files = '%s/%s' % (dst_env.host_site_path, dst_env.files_path)
            run('aws --region=us-west-2 s3 sync %s %s' % (env.s3_bucket, dst_files));
    print('+ Files synced to %s' % dst_env.files_path)
