from fabric.api import task, env, run, execute, require, sudo, prefix, cd, \
    settings\
    as fab_settings
from fabric.contrib.files import exists
from fabric.contrib.console import confirm


@task
def install(branch='master'):
    """ One-time task to install the application in an environment. """

    require('app_path', provided_by=env.available_environments)

    # Uninstall first, if needed
    if exists('%(app_path)s/app' % env):
        if confirm('Previous installation found. Would you like to uninstall '
                   'it?', default=False):
            execute(uninstall)
            print('Uninstalled. Try re-running the install task now.')
            exit()
        else:
            exit()

    print('Installing from branch: %s' % branch)

    # Create log directory
    run('[ -d %(app_path)s/log ] || mkdir %(app_path)s/log' % env)

    # Clone the project repository
    run('if ! [ -d %s/app ]; then git clone -q -b %s %s %s/app; fi' %
        (env.app_path, branch, env.repo_uri, env.app_path))

    with cd(env.app_path + '/app'):
        run('git submodule --quiet update --init --recursive')

    # Setup virtualenv + app's python requirements
    run('if ! [ -d %(app_path)s/venv ]; then virtualenv %(app_path)s/venv;'
        ' fi' % env)

    _install_requirements()

    print('If install succeeded you should run the `deploy` task.')


@task
def uninstall():
    """ Removes the app from an environment. """
    require('app_path', provided_by=env.available_environments)
    with fab_settings(warn_only=True):
        run('rm -rf %(app_path)s/app && rm -rf %(app_path)s/venv' % env)


@task
def deploy(ref='origin/master'):
    """ Deploy a version of the application into an installed environment. """
    require('host_type', 'app_path', provided_by=env.available_environments)

    if not exists('%(app_path)s/app' % env):
        if confirm('No installation found. Would you like to run the install '
                   'task?', default=False):
            execute(install)
            exit('Installed. Try the deploy task now.')
        else:
            exit()

    with cd(env.app_path + '/app'):
        run('git fetch -q && git checkout -f %s' % ref)
        run('git submodule --quiet update --init --recursive')

    _install_requirements()

    # Django tasks
    with cd(env.app_path + '/app'):
        with prefix('source ../venv/bin/activate'):
            run('python manage.py syncdb '
                '--settings=%(django_settings_module)s --noinput' % env,
                warn_only=True)
            run('python manage.py migrate '
                '--settings=%(django_settings_module)s --noinput'
                % env, warn_only=True)
            run('mkdir -p static && python manage.py collectstatic '
                '--settings=%(django_settings_module)s --clear --noinput '
                '--verbosity 0'
                % env)

    # Restart services
    sudo('service uwsgi restart && service nginx restart && service '
         'memcached restart', warn_only=True)


@task
def manage(cmd):
    """ Run a `manage.py` command on an installed environment. """
    require('app_path', 'django_settings_module',
            provided_by=env.available_environments)
    with cd(env.app_path + '/app'):
        with prefix('source ../venv/bin/activate'):
            run('python manage.py {cmd} --settings={settings}'.format(
                cmd=cmd, settings=env.django_settings_module
                ))

@task
def log(how_many=1):
    """ Log the most recent {how_many} commits from the repo on the environment """
    require('app_path', provided_by=env.available_environments)
    with cd(env.app_path + '/app'):
        run('git log -{how_many}'.format(how_many=int(how_many)))


################################################################################
# Task helpers
################################################################################

def _install_requirements():
    require('host_type', 'app_path', provided_by=env.available_environments)
    with prefix('cd %(app_path)s && source venv/bin/activate' % env):
        run('pip install -q -U distribute')
        run('pip install -q -r app/requirements/%(host_type)s.txt' % env)
