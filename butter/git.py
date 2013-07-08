from __future__ import with_statement
from fabric.api import env, cd, abort, hide
from fabric.operations import run


def check_commit(ref):
    print('+ Ensuring %s exists in %s' % (ref, env.host_string))
    with cd('%s/private/repo' % env.host_site_path):
        run('git fetch')
        result = run('git rev-parse %s' % ref)
        if result.failed:
            abort('Commit %s doesnt exist' % ref)
        else:
            return result


def checkout(parsed_ref):
    print('+ Preparing %s for deployment' % parsed_ref)
    with cd(env.host_site_path + '/private/repo'):
        with hide('running', 'stdout'):
            run("""git reset --hard %s && git submodule update --init \
                    --recursive""" % parsed_ref)
    with cd(env.host_site_path):
        run("""mkdir changesets/%s && tar cf - private/repo \
                | (cd changesets/%s; tar xpf -  --strip-components=2)"""
                % (parsed_ref, parsed_ref))
    with cd('%s/changesets/%s' % (env.host_site_path, parsed_ref)):
        run('rm -rf .git*')


def checkout_simple(parsed_ref):
    """ checksout a ref from `private/repo` into `public` """
    print('+ Preparing %s for deployment' % parsed_ref)
    run('rm -rf %s/* %s/.git' % (env.host_site_path, env.host_site_path))
    run('git clone %s %s' % (env.repo, env.host_site_path))
    with cd(env.host_site_path):
        run('git reset --hard %s' % parsed_ref)
        run('git submodule update --init --recursive')
        run('rm -rf .git*')
