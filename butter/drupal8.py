from __future__ import with_statement
from fabric.api import task, env, cd, hide, execute, settings
from fabric.operations import run, prompt, put

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
        run_args = {'capture': True}
        cd_function = lcd

        # Ensure drupal.build can be run in any directory locally.
        import os
        env.host_site_path = os.path.dirname(env.real_fabfile)
    else:
        run_function = run
        run_args = {'quiet': True}
        cd_function = cd

    with cd_function(env.host_site_path + '/' + env.public_path):
         run_function("drush si --yes %s --site-name='%s' --site-mail='%s' --account-name='%s' --account-pass='%s' --account-mail='%s'" %
                 (env.site_profile, env.site_name, 'noreply@ombuweb.com', 'system', 'pass', 'noreply@ombuweb.com'))
         if dev == 'yes':
             run_function("drush en -y %s" % env.dev_modules)
             run_function("drush cr")