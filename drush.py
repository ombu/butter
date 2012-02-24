from __future__ import with_statement
from fabric.api import task, env
from fabric.operations import run

@task
def cc():
    print('+ Running drush cc')
    with cd('%s/current' % env.host_site_path):
        with hide('running', 'stdout'):
            run('drush cc all')

@task
def updatedb():
    print('+ Running drush updatedb')
    with cd('%s/current' % env.host_site_path):
        with hide('running', 'stdout'):
            run('drush updatedb')

@task
def cron():
    print('+ Running drush cron')
    with cd('%s/current' % env.host_site_path):
        with hide('running'):
            run('drush cron')

@task
def migrate():
    print('+ Running migrations')
    with cd('%s/current' % env.host_site_path):
        with hide('running'):
            run('drush migrate-import genre,rating,format,movies,games')

@task
def migrate_rollback():
    print('+ Rolling back migrations')
    with cd('%s/current' % env.host_site_path):
        with hide('running'):
            run('drush migrate-rollback --all')

@task
def solrindex():
    print('+ Rebuilding Solr index')
    with cd('%s/current' % env.host_site_path):
        with hide('running'):
            run('drush solr-delete-index && drush solr-mark-all && drush solr-index')

@task
def rebuild():
    print('Rebuilding the site profile')
    with cd('%s/current' % env.host_site_path):
        run('sh ../private/reset.sh -d')

