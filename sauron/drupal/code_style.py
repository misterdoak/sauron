import datetime
import os

from sauron import utils
from fabric.api import env, task, local, settings


@task
def check_codestyle(email=False):
    """
    Check code style via PHPMess Detector and PHP Code Sniffer

    email -- Send report by email if True.
    """

    project_foler = env.sauron['application']['sandbox_path'] + '/' + env.project['name']
    report_foler = env.sauron['application']['report_path'] + '/' + env.project['name']
    cs_report = report_foler + '/' + datetime.datetime.now().strftime("%Y%m%d%H%M") + '_cs_report.csv'
    phpmd_report = report_foler + '/' + datetime.datetime.now().strftime("%Y%m%d%H%M") + '_phpmd_report.txt'

    phpcs_standard = env.project['drupal']['code_style']['phpcs_standard']
    phpmd_rules_file = env.project['drupal']['code_style']['phpmd_rules_file']

    phpcs_ext_args = ""
    phpmd_ext_args = ""
    if 'phpcs_extra_args' in env.project['drupal']['code_style']:
        phpcs_ext_args = env.project['drupal']['code_style']['phpcs_extra_args']
    if 'phpmd_extra_args' in env.project['drupal']['code_style']:
        phpmd_ext_args = env.project['drupal']['code_style']['phpmd_extra_args']

    local('mkdir -p ' + report_foler)

    with settings(warn_only=True):
        for path in env.project['drupal']['dev_paths']:
            dev_path = project_foler + '/' + env.project['drupal']['drupal_root'] + '/' + path
            local('phpcs -s --report=csv --standard=' + phpcs_standard + ' --extensions=inc,install,module,tpl.php ' + phpcs_ext_args + ' ' + dev_path + ' >> ' + cs_report)
            local('phpmd ' + dev_path + ' text ' + phpmd_rules_file + ' ' + phpmd_ext_args + ' >> ' + phpmd_report)

    if email:
        subject = '[' + env.project['project'] + '] Code style report'
        body = ''
        files = []
        if os.path.exists(cs_report):
            files.append(cs_report)
        if os.path.exists(phpmd_report):
            files.append(phpmd_report)

        mail_server = utils.get_mail_server(env.sauron)
        utils.send_mail(env.sauron['administrator']['mail'], env.project['mail'], subject, body, files, server=mail_server)