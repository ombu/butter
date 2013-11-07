from fabric.api import task, env, execute, settings
from fabric.operations import run, local, prompt
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

@task
def db(src, dst):
    """
    Copies a database from `src` to `dst` environment.
    """
    if src == 'local':
        abort('Cannot sync from local.')
    if dst == 'production':
      force_push = prompt('Are you sure you want to push to production (WARNING: this will destroy production db):', None, 'n', 'y|n')
      if force_push == 'n':
        abort('Sync aborted')

    # record the environments
    execute(dst)
    dst_env = copy(env)
    execute(src)
    src_env = copy(env)

    # Drop the previous tables in dst in case it has tables not in src.
    drop_tables_sql = """mysql -h %(db_host)s -u%(db_user)s -p%(db_pw)s -BNe "show tables" %(db_db)s \
        | tr '\n' ',' | sed -e 's/,$//' \
        | awk '{print "SET FOREIGN_KEY_CHECKS = 0;DROP TABLE IF EXISTS " $1 ";SET FOREIGN_KEY_CHECKS = 1;"}' \
        | mysql -h %(db_host)s -u%(db_user)s -p%(db_pw)s %(db_db)s"""
    local(drop_tables_sql % {"db_host": dst_env.db_host,
        "db_user": dst_env.db_user, "db_pw": dst_env.db_pw,
        "db_db": dst_env.db_db})

    dump_sql = 'mysqldump -h %s -u%s -p%s %s' % (src_env.db_host,
            src_env.db_user, src_env.db_pw, src_env.db_db)
    import_sql = 'mysql -h %s -u%s -p%s -D%s' % (dst_env.db_host,
            dst_env.db_user, dst_env.db_pw, dst_env.db_db)
    local('%s | %s' % (dump_sql, import_sql))
    print('+ Database synced from %s to %s' % (src, dst))
