from __future__ import with_statement
from fabric.api import task, env, cd, settings, hide
from fabric.operations import run

@task
def cc():
    print('+ Running drush cc')
    _drush('cc all')

@task
def updatedb():
    print('+ Running drush updatedb')
    _drush('updatedb')

@task
def cron():
    print('+ Running drush cron')
    _drush('cron')

@task
def migrate(migrations):
    print('+ Running migrations')
    _drush('migrate-import ' + migrations)

@task
def migrate_rollback():
    print('+ Rolling back all migrations')
    _drush('migrate-rollback --all')

@task
def solrindex():
    print('+ Rebuilding Solr index')
    _drush('solr-delete-index && drush solr-mark-all && drush solr-index')

@task
def _drush(cmd):
    with cd('%s/current' % env.host_site_path):
        with settings(hide('warnings'), warn_only=True):
            run('drush ' + cmd)
