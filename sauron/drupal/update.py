import os
import re
import requests
import datetime
import codecs
from glob import glob

import HTML
import xml.etree.ElementTree as ET

from sauron import utils
from fabric.api import env, task, local


@task
def check_update(send_mail=False):
    """
    Check contrib modules and core updates from source code or from makefile
    send_mail -- True if the report has to be sent by email, False otherwise
    """
    contrib_modules_per_path = {}
    modules_infos_per_path = {}
    if 'drupal_makefile' in env.project['drupal']:
        makefile = env.sauron['application']['sandbox_path'] + '/' + env.project['name'] + '/' \
            + env.project['drupal']['drupal_makefile']
        core_version, contrib_modules = get_core_and_modules_from_makefile(makefile)
        contrib_modules_per_path['contrib modules'] = contrib_modules
    else:
        drupal_root = env.sauron['application']['sandbox_path'] + '/' + env.project['name'] \
            + '/' + env.project['drupal']['drupal_root']
        core_version = get_core_version(drupal_root)
        contrib_modules_per_path = get_contrib_modules(drupal_root)

    core_version_major = core_version.split('.')[0]
    for path, contrib_modules in contrib_modules_per_path.items():
        modules_infos = []
        for module, version in contrib_modules.items():
            info = get_module_update_info(module, version, core_version_major)
            if 'title' in info:
                info['machine_name'] = module
                info['current_version'] = version
                modules_infos.append(info)
        modules_infos_per_path[path] = modules_infos

    core_info = get_module_update_info('drupal', core_version, core_version_major)
    core_info['current_version'] = core_version

    has_sec_issue, body = generate_report(core_info, modules_infos_per_path)

    report_foler = env.sauron['application']['report_path'] + '/' + env.project['name']
    report_file = datetime.datetime.now().strftime("%Y%m%d%H%M") + '_drupal_update_report.html'
    write_html_report(report_foler, report_file, body, env.project['project'])

    if has_sec_issue or send_mail is not False:
        subject = '[' + env.project['project'] + '] Your site may have security issues'
        utils.send_mail(env.sauron['administrator']['mail'], env.project['mail'], subject, body, [], True)


def get_core_and_modules_from_makefile(makefile):
    """
    Extract contrib modules and core version from given drush makefile
    makefile -- makefile file path
    return a list of 2 elements:
        0 => core version
        1 => ['<module name>' => '<module_version>']
    """
    contrib_modules = {}
    with open(makefile, "r") as fichier:
        for line in fichier.readlines():
            drupal_core_re = re.compile('projects\[drupal\]\[version\]\s*=\s*\"([a-z . 0-9]+)\"')
            match_core = drupal_core_re.match(line)
            if match_core:
                drupal_core = match_core.group(1)

            core_prefix_re = re.compile('^core\s*=\s*([7-9.x]+)')
            match_core_prefix = core_prefix_re.match(line)
            if match_core_prefix:
                core_prefix = match_core_prefix.group(1)

            module_re = re.compile('projects\[(?!drupal)([a-z0-9-_]+)\]\[version\]\s*=\s*\"([a-z.0-9-]+)\"')
            match_module = module_re.match(line)
            if match_module:
                contrib_modules[match_module.group(1)] = core_prefix + '-' + match_module.group(2)
    return drupal_core, contrib_modules


def get_core_version(drupal_root):
    """
    Retrieve core version from source code
    drupal_root -- drupal root path
    return core version
    """
    version = ''

    if os.path.exists(drupal_root + '/core'):
        """ Seems to be a 8.x """
        system_module_info = drupal_root + '/core/modules/system/system.info.yml'
    elif os.path.exists(drupal_root + '/modules/system/system.info'):
        """ Seems to be a 6.x or 7.x """
        system_module_info = drupal_root + '/modules/system/system.info'

    core_version_re = re.compile('version[\s:=\'"]+([a-b0-9\.]+)')

    fd = open(system_module_info, "r")
    for line in fd:
        match_core = core_version_re.match(line)
        if match_core:
            version = match_core.group(1)
            break
    return version


def get_contrib_modules(drupal_root):
    """
    Retrieve contrib modules version from source code
    drupal_root -- drupal root path
    return a dict:
        ['<module name>' => '<module_version>']
    """
    contrib_modules_per_path = {}
    for path in env.project['drupal']['contrib_paths']:
        contrib_modules = {}
        contrib = drupal_root + '/' + path
        modules = os.listdir(contrib)

        regex = re.compile('version[\s:=\'"]+([^\'"]+)')

        for name in modules:
            if not name.startswith('.'):
                info = glob(contrib + '/' + name + '/*.info*')
                for f in info:
                    fd = open(f, "r")
                    for line in fd:
                        version = regex.findall(line)
                        if version:
                            basename = os.path.basename(f)
                            name = basename.split('.')[0]
                            contrib_modules[name] = version[0]
            contrib_modules_per_path[path] = contrib_modules
    return contrib_modules_per_path


def get_module_update_info(module, version, core_version_major):
    """ Get module update info from drupal update service

    module -- module name or drupal (for core)
    version -- current module/core version
    core_version_major -- core based version : 6, 7 or 8

    return a dict:
        [
          "title" => module title from update service
          "last_security_fix" => last version containing security fix
          "last_bug_fix" => last version containing bug fix
          "last_security_rank" => security fixes release rank according to branch version
          "last_bug_rank" => bug fixes release rank according to branch version
          "current_rank" => rank of current release according to branch version
        ]
    """
    info = {}
    url = 'http://updates.drupal.org/release-history'

    """ Extract branch number (major version in update service) of module"""
    regex = re.compile(core_version_major + '\.x-(\w)+\.\w+')
    major_version = core_version_major
    if module != 'drupal':
        major_version = regex.findall(version)[0]

    """ Call update service """
    content = requests.get(url + '/' + module + '/' + core_version_major + '.x')

    root = ET.fromstring(content.text.encode('ascii', 'ignore'))
    title = root.find('title')
    if ET.iselement(title):
        releases = root.find('releases')
        recommended_major = root.find('recommended_major')
        if ET.iselement(recommended_major):
            recommended_major = recommended_major.text
        last_bug_fix = ''
        last_security_fix = ''
        last_recommended = ''
        last_bug_rank = 0
        last_security_rank = 0
        current_rank = 0

        rank = 1
        for release in releases.findall('release'):
            major_el = release.find('version_major')
            if ET.iselement(major_el):
                major_v = major_el.text
                v = release.find('version').text
                if _is_an_exception(module, v):
                    continue
                if v == version:
                    current_rank = rank
                if major_v == recommended_major and last_recommended == '':
                    last_recommended = v
                terms = release.findall(".//terms/term")
                for term in terms:
                    if term.find('name').text == 'Release type':
                        release_type = term.find('value').text
                        if major_v == major_version and release_type == 'Bug fixes' and last_bug_fix == '':
                            last_bug_fix = v
                            last_bug_rank = rank
                        elif major_v == major_version and release_type == 'Security update' and last_security_fix == '':
                            last_security_fix = v
                            last_security_rank = rank
                rank += 1

        info['title'] = title.text
        info['last_security_fix'] = last_security_fix
        info['last_security_rank'] = last_security_rank
        info['last_bug_fix'] = last_bug_fix
        info['last_bug_rank'] = last_bug_rank
        info['last_recommended'] = last_recommended
        info['current_rank'] = current_rank

    return info


def generate_report(core_info, modules_infos_per_path):
    """
    Generate HTML report according to given modules and core info

    core_info -- core info returned by get_module_update_info
    module_infos -- list of modules info returned by get_module_update_info

    return 2 elements:
        0 => True if security issue has been detected, False otherwise
        1 => HTML report
    """
    header = ['Module', 'Installed version', 'Last security update version', 'Last bug fix version', 'Last recommended version']
    has_sec_issue = False
    colors = ['#DDFFDD', '#FFFFDD', '#FFCCCC']

    core_table = HTML.Table(header_row=header)
    issue_level = _has_issue(core_info)
    if issue_level == 2:
        has_sec_issue = True
    row = [core_info['title'], core_info['current_version'], core_info['last_security_fix'], core_info['last_bug_fix']]
    trow = HTML.TableRow(row, bgcolor=colors[issue_level])

    core_table.rows.append(trow)

    modules_tables = {}
    for path, module_infos in modules_infos_per_path.items():
        modules_table = HTML.Table(header_row=header)
        for info in module_infos:
            issue_level = _has_issue(info)
            if issue_level == 2:
                has_sec_issue = True

            row = [info['title'], info['current_version'], info['last_security_fix'], info['last_bug_fix'], info['last_recommended']]
            trow = HTML.TableRow(row, bgcolor=colors[issue_level])

            modules_table.rows.append(trow)
        modules_tables[path] = modules_table

    head = "This is the update status report of your site " + env.project['project']
    content = head + "<br /><br /><h1>Core</h1>" + str(core_table) + "<br /><br />"

    for path, modules_table in modules_tables.items():
        content += "<h1>" + path + "</h1>" + str(modules_table) + "<br /><br />"

    return has_sec_issue, content


def write_html_report(report_foler, report_file, body, project_title):
    """
    Write on disk HTML report. Report is based on report.html template.

    report_folder -- report folder path
    report_file -- report filename
    body --  report content
    project_title -- project title

    """
    report_filepath = report_foler + '/' + report_file
    local('mkdir -p ' + report_foler)

    report_fd = codecs.open(report_filepath, encoding="utf-8", mode='w+')
    template_fd = codecs.open('templates/report.html', encoding="utf-8")

    for line in template_fd:
        if '{project}' in line:
            line = line.replace('{project}', project_title)
        elif '{report}' in line:
            line = line.replace('{report}', body)
        report_fd.write(line + '\n')
    report_fd.close()
    template_fd.close()


def _is_an_exception(module, version):
    """
    Check if an exception has been set in project settings file

    module -- module to check
    version -- module version

    return True if that module version has to be ignored by sauron, False otherwise
    """
    is_exception = False
    if 'update' in env.project['drupal'] and 'exceptions' in env.project['drupal']['update']:
        if module in env.project['drupal']['update']['exceptions']:
            v = env.project['drupal']['update']['exceptions'][module]
            if version == v:
                is_exception = True

    return is_exception


def _has_issue(info):
    """
    Helper function to determine if given release has issues

    info -- module info returned by get_module_update_info

    return 0 if no issue was found, 1 for bug fix issue, 2 for security fix issue
    """
    issue_level = 0
    if info['last_security_rank'] != 0 and info['current_rank'] > info['last_security_rank']:
        issue_level = 2
    elif info['last_bug_rank'] != 0 and info['current_rank'] > info['last_bug_rank']:
        issue_level = 1
    return issue_level
