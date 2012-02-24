from fabric.api import task, env
import host,  git, deploy, drush, drupal

# Host settings
@task
def qa():
    """
    QA server settings
    """
    env.hosts = ['ombu@qa.ombuweb.com']
    env.host_type = 'staging'
    env.user = 'ombu'
    env.host_webserver_user = 'www-data'
    env.host_site_path = '/vol/main/foo/bar'
    env.base_url = 'http://qa.ombuweb.com'

    # DB settings
    env.db_db = 'foo'
    env.db_user = 'foo_user'
    env.db_pw = 'bar'
    env.db_host = 'localhost'

@task
def stage():
    """
    Stage server settings
    """
    env.hosts = ['ombu@stage.ombuweb.com']
    env.host_type = 'staging'
    env.user = 'ombu'
    env.host_webserver_user = 'www-data'
    env.host_site_path = '/vol/main/foo/bar'
    env.base_url = 'http://stage.ombuweb.com'

    # DB settings
    env.db_db = 'foo'
    env.db_user = 'foo_user'
    env.db_pw = 'bar'
    env.db_host = 'localhost'
