import subprocess
import logging
import os
# Written Modules
from utils import cmd

def install_repos(mname, cname, repos, repo_dest, pkg_man, proxy):
    # check if there are repos passed for install
    if len(repos) == 0:
        logging.info("REPOS: no repos passed to install\n")
        return

    logging.info(f"REPOS: Installing these repos to {cname}")
    for r in repos:
        args = []
        logging.info(r['alias'] + ': ' + r['url'])
        if pkg_man == "zypper":
            args.append("-D")
            args.append(repo_dest)
            args.append("addrepo")
            args.append("-f")
            args.append("-p")
            if 'priority' in r:
                args.append(r['priority'])
            else:
                args.append('99')
            args.append(r['url'])
            args.append(r['alias'])
        elif pkg_man == "dnf":
            args.append("--setopt=reposdir="+repo_dest)
            args.append("--setopt=logdir=/tmp/dnf_test/log")
            args.append("--setopt=cachedir=/tmp/dnf_test/cache")
            if proxy != "":
                args.append("--setopt=proxy="+proxy)
            args.append("config-manager")
            args.append("--save")
            args.append("--add-repo")
            args.append(r['url'])

        rc = cmd([pkg_man] + args)
        if rc != 0:
            raise Exception("Failed to install repo", r['alias'], r['url'])

        if proxy != "":
            if r['url'].endswith('.repo'):
                repo_name = r['url'].split('/')[-1].split('.repo')[0] + "*"
            elif r['url'].startswith('https'):
                repo_name = r['url'].split('https://')[1].replace('/','_')
            elif r['url'].startswith('http'):
                repo_name = r['url'].split('http://')[1].replace('/','_')
            args = []
            args.append('config-manager')
            args.append('--save')
            args.append("--setopt=reposdir="+repo_dest)
            args.append("--setopt=logdir=/tmp/dnf_test/log")
            args.append("--setopt=cachedir=/tmp/dnf_test/cache")
            args.append('--setopt=*.proxy='+proxy)
            args.append(repo_name)

            rc = cmd([pkg_man] + args)
            if rc != 0:
                raise Exception("Failed to set proxy for repo", r['alias'], r['url'], proxy)

        if "gpg" in r:
            # Using rpm apparently works for both Yum- and Zypper-based distros.
            args = []
            if proxy != "":
                arg_env = os.environ.copy()
                arg_env['https_proxy'] = proxy
            args.append("--root="+mname)
            args.append("--import")
            args.append(r["gpg"])

            rc = cmd(["rpm"] + args)
            if rc != 0:
                raise Exception("Failed to install gpg key for", r['alias'], "at URL", r['gpg'])

def install_base_packages(cname, packages, registry_loc, package_dest, pkg_man, proxy):
    # check if there are packages to install
    if len(packages) == 0:
        logging.warn("PACKAGES: no packages passed to install\n")
        return

    logging.info(f"PACKAGES: Installing these packages to {cname}")
    logging.info("\n".join(packages))

    args = []
    if pkg_man == "zypper":
        args.append("-n")
        args.append("-D")
        args.append(registry_loc)
        args.append("-C")
        args.append("/tmp/image-build")
        args.append("--no-gpg-checks")
        args.append("--installroot")
        args.append(package_dest)
        args.append("install")
        args.append("-l")
        args.extend(packages)
    elif pkg_man == "dnf":
        args.append("--setopt=reposdir="+package_dest+"/etc/yum.repos.d")
        args.append("--setopt=logdir=/tmp/dnf_test/log")
        args.append("--setopt=cachedir=/tmp/dnf_test/cache")
        if proxy != "":
            args.append("--setopt=proxy="+proxy)
        args.append("install")
        args.append("-y")
        args.append("--nogpgcheck")
        args.append("--installroot")
        args.append(package_dest)
        args.extend(packages)

    rc = cmd([pkg_man] + args)
    if rc == 104:
        raise Exception("Installing base packages failed")

    if rc == 107:
        logging.warn("one or more RPM postscripts failed to run")

def remove_base_packages(cname, remove_packages):
    # check if there are packages to remove
    if len(remove_packages) == 0:
        logging.warn("REMOVE PACKAGES: no package passed to remove\n")
        return

    logging.info(f"REMOVE PACKAGES: removing these packages from container {cname}")
    logging.info("\n".join(remove_packages))
    for p in remove_packages:
        args = [cname, '--', 'rpm', '-e', '--nodeps', p]
        cmd(["buildah","run"] + args)

def install_base_package_groups(cname, package_groups, registry_loc, package_dest, pkg_man, proxy):
    # check if there are packages groups to install
    if len(package_groups) == 0:
        logging.warn("PACKAGE GROUPS: no package groups passed to install\n")
        return
    
    logging.info(f"PACKAGE GROUPS: Installling these package groups to {cname}")
    logging.info("\n".join(package_groups))
    args = []

    if pkg_man == "zypper":
        logging.warn("zypper does not support package groups")
    elif pkg_man == "dnf":
        args.append("--setopt=reposdir="+package_dest+"/etc/yum.repos.d")
        args.append("--setopt=logdir=/tmp/dnf_test/log")
        args.append("--setopt=cachedir=/tmp/dnf_test/cache")
        if proxy != "":
            args.append("--setopt=proxy="+proxy)
        args.append("groupinstall")
        args.append("-y")
        args.append("--nogpgcheck")
        args.append("--installroot")
        args.append(package_dest)
        args.extend(package_groups)

    rc = cmd([pkg_man] + args)
    if rc == 104:
        raise Exception("Installing base packages failed")
    
def install_base_commands(cname, commands):
    # check if there are commands to install
    if len(commands) == 0:
        logging.warn("COMMANDS: no commands passed to run\n")
        return

    logging.info(f"COMMANDS: running these commands in {cname}")
    for c in commands:
        logging.info(c['cmd'])
        args = [cname, '--', 'bash', '-c', c['cmd']]
        if 'loglevel' in c:
            if c['loglevel'].upper() == "INFO":
                loglevel = logging.info
            elif c['loglevel'].upper() == "WARN":
                loglevel = logging.warn
            else:
                loglevel = logging.error
        else:
            loglevel = logging.error
        out = cmd(["buildah","run"] + args, stderr_handler=loglevel)

def install_base_copyfiles(cname, copyfiles):
    if len(copyfiles) == 0:
        logging.warn("COPYFILES: no files to copy\n")
        return
    logging.info(f"COPYFILES: copying these files to {cname}")
    for f in copyfiles:
        args = []
        if 'opts' in f:
            for o in f['opts']:
                args.extend(o.split())
        logging.info(f['src'] + ' -> ' + f['dest'])
        args +=  [ cname, f['src'], f['dest'] ]
        out=cmd(["buildah","copy"] + args)
