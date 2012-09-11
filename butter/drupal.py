from __future__ import with_statement
from fabric.api import task, env, cd, hide, execute, settings
from fabric.operations import run, prompt
from fabric.contrib import files
from fabric.contrib import console
from butter import deploy
from butter.host import pre_clean

@task
def push(ref):
    """
    Deploy a commit to a host
    """

    if env.repo_type == 'git':
        from butter import git as repo
    elif env.repo_type == 'hg':
        from butter import hg as repo
    parsed_ref = repo.check_commit(ref)
    deploy.clean()
    build_path = '%s/changesets/%s' % (env.host_site_path, parsed_ref)
    pre_clean(build_path)
    repo.checkout(parsed_ref)
    settings_php(build_path)
    set_perms(build_path)
    link_files(build_path)
    deploy.mark(parsed_ref)

@task
def setup_env():
    """
    Set up the directory structure at env.host_site_path
    """

    print('+ Creating directory structure')
    if files.exists(env.host_site_path):
        if console.confirm('Remove existing directory %s' % env.host_site_path):
            with hide('running', 'stdout'):
                run('rm -rf %s' % env.host_site_path)
        else:
            print('+ Directory not removed and recreated')
            return
    with hide('running', 'stdout'):
        run('mkdir -p %s' % env.host_site_path)
    with cd(env.host_site_path):
        with hide('running', 'stdout'):
            run('mkdir changesets files logs private')
            run('touch logs/access.log logs/error.log')
            print('+ Cloning repository: %s' % env.repo_url)
            run('%s clone %s private/repo' % (env.repo_type, env.repo_url))
            if not 'url' in env:
                env.url = prompt('Please enter the site url (ex: qa4.dev.ombuweb.com): ')
            virtual_host = 'private/%s' % env.url
            if files.exists(virtual_host):
                run('rm %s' % virtual_host)
            virtual_host_contents = """<VirtualHost *:80>

  # Admin email, Server Name (domain name) and any aliases
  ServerAdmin martin@ombuweb.com
  ServerName %%url%%

  # Index file and Document Root (where the public files are located)
  DirectoryIndex index.php
  DocumentRoot %%host_site_path%%/current

  # Custom log file locations
  ErrorLog  %%host_site_path%%/logs/error.log
  CustomLog %%host_site_path%%/logs/access.log combined

  <Directory />

    SetEnv APPLICATION_ENV %%host_type%%
    AllowOverride All

    AuthType Basic
    AuthName "Protected"
    AuthUserFile /mnt/main/qa/htpwd
    Require user dev1

  </Directory>

</VirtualHost>"""
            files.append(virtual_host, virtual_host_contents);
            files.sed(virtual_host, '%%host_site_path%%', env.host_site_path)
            files.sed(virtual_host, '%%host_type%%', env.host_type)
            files.sed(virtual_host, '%%url%%', env.url)
            run('rm %s.bak' % virtual_host)
    print('+ Site directory structure created at: %s' % env.host_site_path)


def settings_php(build_path):
    print('+ Configuring site settings.php')
    with cd('%s/public/sites/default' % build_path):
        file = "settings.%s.php" % env.host_type
        if files.exists(file):
            files.sed(file, '%%DB_DB%%', env.db_db)
            files.sed(file, '%%DB_USER%%', env.db_user)
            files.sed(file, '%%DB_PW%%', env.db_pw)
            files.sed(file, '%%DB_HOST%%', env.db_host)
            if 'base_url' in env:
                files.sed(file, '%%BASE_URL%%', env.base_url)
            if files.exists('settings.php'):
                run('rm settings.php')
            run('cp settings.%s.php settings.php' % env.host_type )
            run('rm settings.*.php settings.*.bak')
        else:
            run('ls -lah')
            abort('Could not find %s' % file)

def set_perms(build_path):
    print('+ Setting Drupal permissions')
    with cd(env.host_site_path):
        run('chown -R %s private logs %s' % (env.user, build_path))
        run('chgrp -R %s %s' % (env.host_webserver_user, build_path))
        run('chmod -R 2750 %s' % build_path)
        run('chmod -R 0700 private logs')
        run('chmod 0440 %s/public/sites/default/settings*' % build_path)

def link_files(build_path):
    print('+ Creating symlinks')
    with cd('%s/public/sites/default' % build_path):
        run('rm -rf files')
        run('ln -s ../../../../../files files')
    with cd(env.host_site_path):
        run('if [ -h current ] ; then unlink current ; fi')
        run('ln -s %s/public current' % build_path)

@task
def set_files_perms():
    """
    Sets proper permissions on site fiies dire
    """
    print('+ Setting permissions for the files directory')
    with cd(env.host_site_path):
        run('chown -R %s files' % env.user)
        run('chgrp -R %s files' % env.host_webserver_user)
        run('chmod -R 2770 files')

@task
def pull(src, dst):
    """
    Moves drupal sites between servers
    """
    import getpass
    from fabric.api import hide
    from fabric.operations import get, put, local
    from copy import copy

    # prompt upfront
    mysql_src_pw = getpass.getpass(
        'Enter the MySQL root password of the `from` server:'
    )
    mysql_dst_pw = getpass.getpass(
        'Enter the MySQL root password of the `to` server:'
    )
    if dst == 'local':
        local_db = prompt('Please enter the name of the local database: ')

    # record the environments
    execute(dst)
    dst_env = copy(env)
    execute(src)
    src_env = copy(env)

    # helper vars
    sqldump = '/tmp/src_%s.sql.gz' % env.db_db
    src_files = '%s/current/sites/default/files/' % src_env.host_site_path

    # grab a db dump
    with settings(host_string=src_env.hosts[0]):
        run('mysqldump -uroot -p%s %s | gzip > %s' %
                (mysql_src_pw, env.db_db, sqldump))
        get(sqldump, sqldump)

    # Pulling remote to local
    if dst == 'local':
        local("""echo 'drop database if exists %s; create database %s;' \
        | mysql -u root -p%s""" % (dst_env.db_db, dst_env.db_db, mysql_dst_pw))
        local("gunzip -c %s | mysql -uroot -p%s -D%s" % (sqldump, mysql_dst_pw,
            dst_env.db_db))
        local("rm %s" % sqldump)
        dst_files = dst_env.public_path + '/sites/default/files/'
        local("""rsync --human-readable --archive --backup --progress \
                --rsh='ssh -p %s' --compress %s@%s:%s %s      \
                --exclude=css --exclude=js --exclude=styles"""
            % (src_env.port, src_env.user, src_env.host, src_files, dst_files))

    # Source and destination environments are in the same host
    elif src_env.hosts[0] == dst_env.hosts[0]:
        with settings(host_string=dst_env.hosts[0]):
            run("""echo 'drop database if exists %s; create database %s;' \
                | mysql -uroot -p%s""" % (dst_env.db_db, dst_env.db_db,
                mysql_dst_pw))
            run("gunzip -c %s | mysql -uroot -p%s -D%s" %
                (sqldump, mysql_dst_pw, dst_env.db_db))
            run("rm %s" % sqldump)
            dst_files = '%s/%s/sites/default/files/' % (dst_env.host_site_path,
                    dst_env.public_path)
            run("""rsync --human-readable --archive --backup --progress \
                    --compress %s %s \
                    --exclude=css --exclude=js --exclude=styles
                    """ % (src_files, dst_files))

    # Pulling remote to remote & remote servers are not the same host
    else:
        with settings(host_string=dst_env.hosts[0]):
            put(sqldump, sqldump)
            run("""echo 'drop database if exists %s; create database %s;' \
                | mysql -u oot -p%s""" % (dst_env.db_db, dst_env.db_db,
                mysql_dst_pw))
            run("gunzip -c %s | mysql -uroot -p%s -D%s" %
                (sqldump, mysql_dst_pw, dst_env.db_db))
            run("rm %s" % sqldump)
            dst_files = '%s/%s/sites/default/files/' % (dst_env.host_site_path,
                    dst_env.public_path)
            run("""rsync --human-readable --archive --backup --progress \
                    --rsh='ssh -p %s' --compress %s:%s %s     \
                    --exclude=css --exclude=js --exclude=styles
                    """ % (src_env.port, src_env.hosts[0], src_files,
                        dst_files))

@task
def rebuild():
    """
    DEPRECATED. Use `drupal.build` instead. This task is leftin the codebase
    for compatibility with site builds that rely on reset.sh.
    """
    print('Rebuilding the site profile')
    with cd(env.host_site_path + '/current'):
        run("""sh ../private/reset.sh -d""", shell=True)

@task
def build(dev='no'):
    """
    Build Drupal site profile (warning: this will delete your current site
    database)
    """
    print('Rebuilding the site')

    # If there's no host defined, assume localhost and run tasks locally.
    if not env.hosts:
        from fabric.operations import local
        from fabric.api import lcd
        run_function = local
        cd_function = lcd
        env.host_site_path = '.'
    else:
        run_function = run
        cd_function = cd

    with cd_function(env.host_site_path + '/' + env.public_path):
        run_function("drush si --yes %s --site-name='%s' --site-mail='%s' --account-name='%s' --account-pass='%s' --account-mail='%s'" %
                (env.site_profile, env.site_name, 'example@ombuweb.com', 'system', 'pass', 'example@ombuweb.com'))
        run_function("chmod 755 sites/default")
        run_function("chmod 644 sites/default/settings.php")
        if dev == 'yes':
            run_function("drush en -y %s" % env.dev_modules)
            run_function("drush cc all")

@task
def force_files_perms():
    from fabric.api import sudo
    print('+ Setting file permissions with sudo')
    with cd(env.host_site_path):
        sudo('chown -R %s:%s files' % (env.user, env.host_webserver_user))
        sudo('chmod -R 2770 files')
