from fabric.api import env, task, local


@task
def checkout():
    """ Checkout project sources according to vcs configured in project YAML file
    """
    vcs_type = env.project['vcs']['type']
    project_folder = env.sauron['application']['sandbox_path'] + '/' + env.project['name']
    if vcs_type == 'svn':
        local('mkdir -p ' + project_folder)
        local('svn co --ignore-externals ' + env.project['vcs']['extra_args']
              + env.project['vcs']['url'] + ' ' + project_folder)
    elif vcs_type == 'git':
        local('rm -rf ' + project_folder)
        local('git clone --depth=1 ' + env.project['vcs']['extra_args'] + ' ' + env.project['vcs']['url'] + ' '
              + project_folder)
