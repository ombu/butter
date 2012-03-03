from __future__ import with_statement
from fabric.api import task, env, cd
from fabric.operations import run

@task
def cc():
    print('+ Running drush cc')
    _drush('drush cc all')

@task
def updatedb():
    print('+ Running drush updatedb')
    _drush('drush updatedb')

@task
def cron():
    print('+ Running drush cron')
    _drush('drush cron')

@task
def migrate():
    print('+ Running migrations')
    _drush('drush migrate-import genre,rating,format,movies,games')

@task
def migrate_rollback():
    print('+ Rolling back migrations')
    _drush('drush migrate-rollback --all')

@task
def solrindex():
    print('+ Rebuilding Solr index')
    _drush('drush solr-delete-index && drush solr-mark-all && drush solr-index')

@task
def rebuild():
    print('Rebuilding the site profile')

def _drush(cmd):
    with cd('%s/current' % env.host_site_path):
        run(cmd)
