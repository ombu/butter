"""
 Copyright (c) 2012, OMBU Inc. http://ombuweb.com
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
     * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
     * Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
     * Neither the name of OMBU INC. nor the
       names of its contributors may be used to endorse or promote products
       derived from this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 ARE DISCLAIMED. IN NO EVENT SHALL OMBU INC. BE LIABLE FOR ANY DIRECT,
 INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
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

