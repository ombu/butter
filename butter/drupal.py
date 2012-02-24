from __future__ import with_statement
from fabric.api import task, env
from fabric.operations import run

@task
def deploy(ref):
    """
    Deploy a commit to a host
    """
    parsed_ref = check_commit(ref)
    build_path = '%s/changesets/%s' % (env.host_site_path, parsed_ref)
    pre_clean(build_path)
    clone_git(parsed_ref)
    settings_php(build_path)
    set_perms(build_path)
    link_files(build_path)
    mark(parsed_ref)

def settings_php(build_path):
    print('+ Configuring site settings.php')
    with cd('%s/public/sites/default' % build_path):
        file = "settings.%s.php" % env.host_type
        if files.exists(file):
            files.sed(file, '%%DB_DB%%', env.db_db)
            files.sed(file, '%%DB_USER%%', env.db_user)
            files.sed(file, '%%DB_PW%%', env.db_pw)
            files.sed(file, '%%DB_HOST%%', env.db_host)
            files.sed(file, '%%DB_LEGACY_CODEBASE%%', env.paramount_legacy_codebase)
            files.sed(file, '%%BASE_URL%%', env.base_url)
            if files.exists('settings.php'):
                run('rm settings.php')
            run('cp settings.%s.php settings.php' % env.host_type )
            run('rm settings.*.php settings.*.bak')
        else:
            run('ls -lah')
            abort('Could not find %s' % file)

def set_perms(build_path):
    print('+ Setting file permissions')
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            sudo('chown -R %s private logs files %s' % (env.user, build_path))
            sudo('chgrp -R %s files %s' % (env.host_webserver_user, build_path))
            sudo('chmod -R 2750 %s' % build_path)
            sudo('chmod -R 2770 files')
            sudo('chmod -R 0700 private logs')
            sudo('chmod 0440 %s/public/sites/default/settings*' % build_path)

def link_files(build_path):
    print('+ Creating symlinks')
    with cd('%s/public/sites/default' % build_path):
        with hide('running', 'stdout'):
            run('rm -rf files')
            run('ln -s ../../../../../files files')
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            run('if [ -h current ] ; then unlink current ; fi')
            run('ln -s %s/public current' % build_path)

@task
def set_files_perms():
    """
    Sets proper permissions on site fiies dire
    """
    print('+ Setting permissions for the files directory')
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            sudo('chown -R %s files' % env.user)
            sudo('chgrp -R %s files' % env.host_webserver_user)
            sudo('chmod -R 2770 files')

@task
def pull(to='local'):
    """
    Moves drupal sites between servers
    """
    import getpass
    mysql_from = getpass.getpass('Enter the MySQL root password of the `from` server:')
    mysql_to = getpass.getpass('Enter the MySQL root password of the `to` server:')
    sqldump = '/tmp/foobar.sql.gz'
    with hide('running'):
        run('mysqldump -uroot -p%s %s | gzip > %s' % (mysql_from, env.db_db, sqldump))
    get(sqldump, sqldump)

    remote_files = '%s/current/sites/default/files/' % env.host_site_path

    if to == 'local':
        local("echo 'drop database if exists pmount; create database pmount;' | mysql -u root -p%s" % mysql_to)
        local("gunzip -c %s | mysql -uroot -p%s -Dpmount" % (sqldump, mysql_to))
        local("rm %s" % sqldump)
        local_files = 'public/sites/default/files/'
        local("""rsync --human-readable --archive --backup --progress \
                --rsh='ssh -p %s' --compress %s@%s:%s %s      \
                --exclude=css --exclude=js --exclude=styles
              """ % (env.port, env.user, env.host, remote_files, local_files))
    else:
        import sys
        # call the environment
        getattr(sys.modules[__name__], to)()
        put(sqldump, sqldump)
        run("echo 'drop database if exists pmount; create database pmount;' | mysql -u root -p%s" % mysql_to)
        run("gunzip -c %s | mysql -uroot -p%s -Dpmount" % (sqldump, mysql_to))
        run("rm %s" % sqldump)
        run("""rsync --human-readable --archive --backup --progress \
                --rsh='ssh -p %s' --compress %s@%s:%s %s/files/     \
                --exclude=css --exclude=js --exclude=styles
                """ % (env.port, env.user, env.host, remote_files, env.host_site_path))
