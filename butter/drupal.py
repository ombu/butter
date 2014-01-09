from __future__ import with_statement
from fabric.api import task, env, cd, hide, execute, settings
from fabric.operations import run, prompt
from fabric.contrib import files
from fabric.contrib import console
from urlparse import urlparse
from butter import deploy, sync as butter_sync
from butter.host import pre_clean
from .drush import solrindex

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
        with hide('stdout'):
            run('mkdir changesets files private')
            print('+ Cloning repository: %s' % env.repo_url)
            run('ssh-keyscan -H github.com >> ~/.ssh/known_hosts')
            run('ssh-keyscan -H bitbucket.org >> ~/.ssh/known_hosts')
            run('%s clone --quiet %s private/repo' % (env.repo_type,
                                                      env.repo_url))
        run('chmod g+w private/repo')
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
            if 'smtp_pw' in env:
              files.sed(file, '%%SMTP_PW%%', env.smtp_pw)
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
        run('chown %s:%s %s && chgrp -R %s %s' % (env.user,
            env.host_webserver_user, build_path, env.host_webserver_user,
            build_path))
        run('chmod -R 2770 %s' % build_path)
        run('chmod 0440 %s/public/sites/default/settings*' % build_path)

def link_files(build_path):
    print('+ Creating symlinks')
    ensure_files_path()
    with cd(build_path):
        run('rm -rf %s' % env.files_path)
        run('ln -s %s/files %s' % (env.host_site_path, env.files_path))
    with cd(env.host_site_path):
        run('if [ -h current ] ; then unlink current ; fi')
        run('ln -s %s/public current' % build_path)

@task
def sync_files(dst, opts_string=''):
    """
    Syncs Drupal files from the environment's S3 bucket to `dst`.
    """
    ensure_files_path()
    exclude = ['*styles/*', '*xmlsitemap/*', '*js/*', '*css/*', '*ctools/*']
    opts_string += ' ' + ' '.join(["--exclude '%s'" % v for v in exclude])
    butter_sync.files(dst, opts_string)

@task
def sync_db(src, dst):
    """
    Copies a Drupal database from `src` to `dst` environment.
    """
    butter_sync.db(src, dst)

@task
def sync(src, dst):
    """
    Moves drupal sites between servers
    """
    sync_db(src, dst);
    sync_files(dst);
    print('+ Site synced from %s to %s' % (src, dst))

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
def build(dev='yes'):
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

        # Ensure drupal.build can be run in any directory locally.
        import os
        env.host_site_path = os.path.dirname(env.real_fabfile)
    else:
        run_function = run
        cd_function = cd

    with cd_function(env.host_site_path + '/' + env.public_path):
         run_function("drush si --yes %s --site-name='%s' --site-mail='%s' --account-name='%s' --account-pass='%s' --account-mail='%s'" %
                 (env.site_profile, env.site_name, 'noreply@ombuweb.com', 'system', 'pass', 'noreply@ombuweb.com'))
         if dev == 'yes':
             run_function("drush en -y --skip %s" % env.dev_modules)
             run_function("drush cc all")

         run_function("chmod 2770 sites/default")

         # Rebuild solr, since apachesolr.module will reindex all newly created
         # nodes, possibly creating duplicate content in the solr index.
         # @todo: remove direct calls to drush and replace with execute() once
         # global local vs. remote context has been figured out.
         # execute(solrindex);
         with settings(hide('warnings'), warn_only=True):
             run_function('drush solr-delete-index && drush solr-mark-all && drush solr-index')

@task
def enforce_perms():
    from fabric.api import sudo
    print('+ Setting file permissions with sudo')
    with cd(env.host_site_path):
        sudo('chown -R %s:%s files && chmod -R 2770 files' % (env.user,
            env.host_webserver_user))

def ensure_files_path():
    if not 'files_path' in env:
        env.files_path = 'public/sites/default/files'
