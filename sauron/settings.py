import yaml

from fabric.api import env, task

@task
def load_settings(project):
    """Load main settings and given project specific settings
       project -- project name, same as yaml file name
    """
    stream = open('config/sauron.yml', 'r')
    env.sauron = yaml.load(stream)

    stream = open(env.sauron['application']['projects_path'] + '/' + project + '.yml', 'r')
    env.project = yaml.load(stream)
    env.project['name'] = project
