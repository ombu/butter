from fabric.api import task, env
import host,  git, deploy, drush, drupal

env.repo_type = 'git'
env.repo_url = ''
env.use_ssh_config = 'true'

# Global environment settings
env.site_name = 'New Site'
env.public_path = 'public'
env.site_profile = 'profile'

env.s3_bucket = 'files.s3domain.com'
env.s3_namespace = 'site_namespace'

# Host settings
@task
def local():
    """
    The local host definition
    """
    env.db_db = 'foo'
    env.db_user = 'foo_user'
    env.db_pw = 'bar'
    env.db_host = 'localhost'
    env.files_path = 'public/sites/default/files'

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
    env.files_path = 'files'
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
    env.files_path = 'files'
    env.base_url = 'http://stage.ombuweb.com'

    # DB settings
    env.db_db = 'foo'
    env.db_user = 'foo_user'
    env.db_pw = 'bar'
    env.db_host = 'localhost'
