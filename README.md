![Sauron logo](https://raw.githubusercontent.com/misterdoak/sauron/master/images/sauron.png)
Sauron
=======

> + You are a **Drupal** developper and you need to be aware of modules and core updates? **Sauron can help you!**

> + You maintain a bunch of **Drupal** Web sites and need to get updates reports? **Sauron can help you!**

> + You only have the source code of a **Drupal** project and need to get a summary of modules and core version? **Sauron can help you!**

> + ...

About
=====

Sauron is a python 2.7 application built on top of [Fabric framework](http://www.fabfile.org/). It provides a few tasks to deal with Drupal :
+ Generate a report of available updates for modules and core
+ Run PHP_CodeSniffer and PHP_MessDetector of specific developpment

Example of HTML report

![Capture-1](https://raw.githubusercontent.com/misterdoak/sauron/master/images/capture-1.png)


Install
=======

On Debian based distribution
```
#>sudo aptitude install python2.7 python2.7-dev python-pip build-essential
#>sudo pip install fabric pyyaml requests HTML.py
#>git clone git@github.com:misterdoak/sauron.git
```

After installing Sauron, you need to copy main settings file : *config/sauron_example.yml* into *config/sauron.yml* and then edit it.
```
{
    "administrator": {
        "mail": "<sender email reports>",
        "mail_signature": {
            "html": "<em>-- This email is automatically generated by sauron.<em>",
            "text": "This email is automatically generated by sauron."
        }
    },
    "application": {
        "projects_path": "<path where projects files are stored>",
        "sandbox_path": "<path where projects are checkout>",
        "report_path": "<path where reports wiil be stored>"
    }
}
```

Using Sauron for your project(s)
==============================


For each project, you will need to create a <choose_name_project>.yml file. This contains information about your project :
+ project : project name
+ mail : list of recepients for sending report
+ vcs : Sauron can fetch sources from Git OR Subversion
    + type : svn or git
    + url : svn url or git url
    + extra_args : extra arguments inserting in vcs checkout command
+ drupal :
    + drupal_root : drupal root path relative to source code root path
    + contrib_paths : a list of contrib modules paths relative to drupal root path
    + drupal_makefile : path to makefile relative to drupal root path
    + dev_paths : a list of specific modules paths relative to drupal root path
    + code_style :
        + phpcs_standard : path to PHP Code Sniffer Settings
        + phpmd_rules_file : path to PHP Mess Detectors rules file


For example :
```
{
    "project": "My project",
    "mail": ["<email>"],

    "vcs": {
        "type": "svn",
        "url": "https://github.com/misterdoak/sauron/trunk",
        "extra_args": ""
    },

    "drupal": {
        "drupal_root": "examples/no_makefile/drupal-7.32",
        "contrib_paths": ["sites/all/modules/contrib"],
        "dev_paths": ["sites/all/themes/custom"],
        "code_style":{
          "phpcs_standard":"/home/almor/phpqa/codesniffer/Drupal",
          "phpmd_rules_file":"/home/almor/phpqa/phpmd/phpmd.xml",
        }
    }
}
```

Here is an example of a git project using a makefile :
```

{
        "project": "My project",
        "mail": ["<email>"],

        "vcs": {
            "type": "git",
            "url": "git@github.com:misterdoak/sauron.git",
            "extra_args": "-b master"
        },

        "drupal": {
            "drupal_makefile": "examples/makefile/sauron.make"
        }
}
```

Launch tasks
=============
Tasks must be launched through Fabric fab command in the same folder of fabfile.py.

List available tasks
--------------------
```
#>fab -l
Available commands:

    code_style.check_codestyle  Check code style via PHPMess Detector and PHP...
    settings.load_settings      Load main settings and given project specific...
    update.check_update         Check contrib modules and core updates from s...
    versionning.checkout        Checkout project sources according to vcs con...
```

Launch Drupal updates check
---------------------------
```
#>fab settings.load_settings:project=myproject_git versionning.checkout update.check_update:send_mail=True
```
Launch Drupal code style check
-------------------------------
```
#>fab settings.load_settings:project=myproject_git versionning.checkout code_style.check_codestyle:email=True
```
Schedule Drupal updates check every Thursday morning
----------------------------------------------------
Security issues are published every Wednesday, you can check every Thursday, early in the morning, modules updates
availability.
To do that, edit your crontab :
```
0 1 * * 4 <user> cd /path/to/sauron && fab settings.load_settings:project=myproject_git versionning.checkout update.check_update:send_mail=True > /dev/null 2>&1
```

Roadmap
========
+ Add hacked check - Check if a contrib module or core has been modified
+ Propose other report formats other than HTML
