from __future__ import with_statement
from fabric.api import task, env, cd, hide
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
    if not files.exists('%s/private/repo' % env.host_site_path):
        setup_env()
    if env.repo_type == 'git':
        from butter import git as repo
    elif env.repo_type == 'hg':
        from butter import hg as repo
    parsed_ref = repo.check_commit(ref)
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
            run('mkdir changesets')
            run('mkdir files')
            run('mkdir logs')
            run('touch logs/access.log')
            run('touch logs/error.log')
            run('mkdir private')
            print('+ Cloning repository: %s' % env.repo_url)
            run('%s clone %s private/repo' % (env.repo_type, env.repo_url))
            url = prompt('Please enter the site url (ex: qa4.dev.ombuweb.com): ')
            virtual_host = 'private/%s' % url
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
            files.sed(virtual_host, '%%url%%', url)
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
    from fabric.api import sudo
    print('+ Setting file permissions')
    with cd(env.host_site_path):
        sudo('chown -R %s private logs files %s' % (env.user, build_path))
        sudo('chgrp -R %s files %s' % (env.host_webserver_user, build_path))
        sudo('chmod -R 2750 %s' % build_path)
        sudo('chmod -R 2770 files')
        sudo('chmod -R 0700 private logs')
        sudo('chmod 0440 %s/public/sites/default/settings*' % build_path)

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
        sudo('chown -R %s files' % env.user)
        sudo('chgrp -R %s files' % env.host_webserver_user)
        sudo('chmod -R 2770 files')

@task
def pull(to='local'):
    """
    Moves drupal sites between servers
    """
    import getpass
    from fabric.api import hide
    from fabric.operations import get, put, local
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
        locals()[to]()
        put(sqldump, sqldump)
        run("echo 'drop database if exists pmount; create database pmount;' | mysql -u root -p%s" % mysql_to)
        run("gunzip -c %s | mysql -uroot -p%s -Dpmount" % (sqldump, mysql_to))
        run("rm %s" % sqldump)
        run("""rsync --human-readable --archive --backup --progress \
                --rsh='ssh -p %s' --compress %s@%s:%s %s/files/     \
                --exclude=css --exclude=js --exclude=styles
                """ % (env.port, env.user, env.host, remote_files, env.host_site_path))

@task
def rebuild():
    print('Rebuilding the site profile')
    with cd(env.host_site_path + '/current'):
      run("""sh ../private/reset.sh -d""")
