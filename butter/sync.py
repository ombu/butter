from fabric.api import task, env, execute, settings
from fabric.operations import run, local, prompt
from fabric.utils import abort
from boto.s3.connection import S3Connection
from datetime import datetime, timedelta
from time import time

@task
def files(dst='local', opts_string=''):
    """
    Syncs files from the environment's S3 bucket to `dst` env.files_path.
    """
    if dst == 'production':
        abort('Cannot sync to production.')
    if not 's3_bucket' in env:
        abort('Please configure an env.s3_bucket for this project.')

    # TODO: Move region into individual push/pull f, reading from
    # global settings.
    opts_string += ' --region=us-west-2'

    push_files_to_s3(opts_string)
    execute(dst)
    pull_files_from_s3(opts_string)
    execute(get_source_environment())

def push_files_to_s3(opts_string=''):
    """
    Sync files from current environment to S3
    """
    s3_directory = 's3://' + env.s3_bucket + '/' + _get_s3_bucket('files')
    src_files = env.host_site_path + '/' + env.files_path
    run('aws s3 sync %s %s %s'
        % (opts_string, src_files, s3_directory))

def pull_files_from_s3(opts_string=''):
    """
    Sync files from S3 to dst
    """
    s3_directory = 's3://' + env.s3_bucket + '/' + _get_s3_bucket('files')

    if not 'files_path' in env:
        abort('`files_path` not found in env.')

    if env.host_type == 'local':
        # Ensure drupal.sync works anywhere in project structure by getting the
        # directory that the fabfile is in (project root).
        import os
        dst_files = os.path.dirname(env.real_fabfile) + '/' + env.files_path
        local('aws s3 sync %s %s %s'
              % (s3_directory, dst_files, opts_string))
    else:
        with settings(host_string=env.hosts[0]):
            dst_files = '%s/%s' % (env.host_site_path, env.files_path)
            run('aws s3 sync %s %s %s'
                % (s3_directory, dst_files, opts_string))

    print '+ Files synced to %s' % env.files_path

@task
def db(dst='local', opts_string=''):
    """
    Copies a database from environment's S3 bucket to `dst` environment.
    """
    src = get_source_environment()

    if src == 'local':
        abort('Cannot sync from local.')

    if dst == 'production':
        force_push = prompt(
            'Are you sure you want to push to production (WARNING: this will'
            ' destroy production db):', None, 'n', 'y|n')
        if force_push == 'n':
            abort('Sync aborted')

    if not 's3_bucket' in env:
        abort('Please configure an env.s3_bucket for this project.')

    try:
        dump_path = find_s3_db_dump(prompt_db=True)
    except DumpNotFound:
        dump_path = push_db_to_s3()

    execute(dst)

    pull_db_from_s3(dump_path)

    execute(src)

    print '+ Database synced from %s to %s' % (src, dst)

def find_s3_db_dump(day_granularity=5, prompt_db=False):
    """
    Attempts to find a valid dump in S3 within the day granularity

    If configured, will prompt user to accept dump as valid
    """

    # @todo: warn user if can't connection
    connection = S3Connection()
    bucket = connection.lookup(env.s3_bucket)
    if bucket is None:
        abort('Bucket %s not found in S3' % env.s3_bucket)

    s3_directory = _get_s3_bucket()
    keys = bucket.list(s3_directory, "/")
    date_format = "%Y-%m-%dT%H:%M:%S"
    date_limit = datetime.today() - timedelta(days=day_granularity)
    valid_dump = False
    if list(keys):
        for key in _filter_s3_files(keys):
            if datetime.strptime(key.last_modified[:19], date_format) >= date_limit:
                if prompt_db:
                    accept_dump = prompt(
                        'A database dump has been found from %s. Do you want '
                        'to import this dump ("n" will generate a new dump)?'
                        % (key.last_modified), default='y', validate='y|n'
                    )
                else:
                    accept_dump = 'y'

                if accept_dump == 'y':
                    valid_dump = 's3://' + env.s3_bucket + '/' + key.name
                break

    if not valid_dump:
        raise DumpNotFound()

    return valid_dump

class DumpNotFound(Exception):
    pass

def push_db_to_s3():
    """
    Creates a new DB dump from environment and pushes to S3
    """

    # TODO: Get global setting
    opts_string = ' --region=us-west-2'

    src = get_source_environment()

    dump_sql = 'mysqldump -h %s -u%s -p%s %s' % (
        env.db_host, env.db_user, env.db_pw, env.db_db
    )
    valid_dump = 's3://%s/%s%s.sql.gz' % (
        env.s3_bucket, _get_s3_bucket(), datetime.today().strftime('%Y%m%d')
    )
    tmp_file = '/tmp/%s-%s.%d.sql.gz' % (env.s3_namespace, src, int(time()))
    run(
        '%(dump_sql)s | gzip -c > %(tmp)s &&'
        'aws s3 cp %(opts)s %(tmp)s %(dump)s && rm %(tmp)s' % {
            'dump_sql': dump_sql,
            'tmp': tmp_file,
            'opts': opts_string,
            'dump': valid_dump
        }
    )

    return valid_dump

def pull_db_from_s3(dump):
    """
    Pulls database from S3 to dst
    """

    # TODO: Get global setting
    opts_string = ' --region=us-west-2'

    # If there's no host defined, assume localhost and run tasks locally.
    if env.host_type == 'local':
        run_function = local
    else:
        run_function = run

    # Drop the previous tables in dst in case it has tables not in src.
    drop_tables_sql = """mysql -h %(db_host)s -u%(db_user)s -p%(db_pw)s \
        -BNe "show tables" %(db_db)s \
        | tr '\n' ',' | sed -e 's/,$//' \
        | awk '{print "SET FOREIGN_KEY_CHECKS = 0;DROP TABLE IF EXISTS " $1 ";SET FOREIGN_KEY_CHECKS = 1;"}' \
        | mysql -h %(db_host)s -u%(db_user)s -p%(db_pw)s %(db_db)s"""

    run_function(drop_tables_sql % {
        "db_host": env.db_host,
        "db_user": env.db_user,
        "db_pw": env.db_pw,
        "db_db": env.db_db
        })

    import_sql = 'mysql -h %s -u%s -p%s -D%s' % (
        env.db_host, env.db_user, env.db_pw, env.db_db
    )
    tmp_file = '/tmp/%s-%s.%d.sql.gz' % (
        env.s3_namespace, env.host_type, int(time())
    )
    run_function('aws s3 cp %(opts)s %(dump)s %(tmp)s && gunzip -c %(tmp)s |'
                 '%(import_sql)s && rm %(tmp)s' % {
                     'opts': opts_string,
                     'dump': dump,
                     'tmp': tmp_file,
                     'import_sql': import_sql
                 })

def _get_s3_bucket(bucket_type='db'):
    """
    Returns namespaced bucket path for environment
    """

    src = get_source_environment()
    return env.s3_namespace + '.' + src + '/' + bucket_type + '/'

def _filter_s3_files(keys):
    """
    Filters out directories from a list of S3 keys
    """
    return (key for key in keys if not key.name.endswith('/'))

def get_source_environment():
    """
    Not the prettiest way to get the source environment because it assumes
    it's the first task called, but good enough for now.
    """
    return env.tasks[0]
