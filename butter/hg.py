from __future__ import with_statement
from fabric.api import env, cd
from fabric.operations import run

def check_commit(ref):
    print('+ Ensuring %s exists in %s' % (ref, env.host_string))
    with cd('%s/private/repo' % env.host_site_path):
        run('hg pull')
        result = run('hg identify --id -r %s' % ref)
        if result.failed:
            abort('Commit %s doesnt exist' % ref)
        else:
            return result

def checkout(parsed_ref):
     print('+ Preparing %s for deployment' % parsed_ref)
     with cd(env.host_site_path + '/private/repo'):
         run('hg archive --rev %s ../../changesets/%s' % (parsed_ref, parsed_ref))
     with cd('%s/changesets/%s' % (env.host_site_path, parsed_ref)):
         run('rm -rf .hg*')
