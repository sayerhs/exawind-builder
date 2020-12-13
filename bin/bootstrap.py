# -*- coding: utf-8 -*-

"""\
ExaWind build bootstrap file
"""

import sys
import os
import glob
import json
import argparse
import subprocess
import shlex
from contextlib import contextmanager

def abspath(pname):
    """Return the absolute path of the directory.
    This function expands the user home directory as well as any shell
    variables found in the path provided and returns an absolute path.
    Args:
        pname (path): Pathname to be expanded
    Returns:
        path: Absolute path after all substitutions
    """
    pth1 = os.path.expanduser(pname)
    pth2 = os.path.expandvars(pth1)
    return os.path.normpath(os.path.abspath(pth2))

def ensure_directory(dname):
    """Check if directory exists, if not, create it.
    Args:
        dname (path): Directory name to check for
    Returns:
        Path: Absolute path to the directory
    """
    abs_dir = abspath(dname)
    if not os.path.exists(abs_dir):
        os.makedirs(abs_dir)
    return abs_dir

@contextmanager
def working_directory(dname, create=False):
    """A with-block to execute code in a given directory.
    Args:
        dname (path): Path to the working directory.
        create (bool): If true, directory is created prior to execution
    Returns:
        path: Absolute path to the execution directory
    """
    abs_dir = abspath(dname)
    if create:
        ensure_directory(abs_dir)

    orig_dir = os.getcwd()
    try:
        os.chdir(abs_dir)
        yield abs_dir
    finally:
        os.chdir(orig_dir)

def clone_repo(repo, basedir, recursive=False):
    """Clone a repository"""
    cmd = "git clone %s %s"%('--recurse-submodules' if recursive else '', repo)
    print("==> Cloning repo: %s"%cmd)
    cmd_lst = shlex.split(cmd)
    with working_directory(basedir, create=False):
        try:
            subprocess.check_call(cmd_lst)
            return True
        except subprocess.CalledProcessError:
            return False

class Bootstrap:
    """Bootstrap exawind-builder"""

    #: Description for command line help message
    description = "ExaWind Builder"

    #: Default location for installing exawind project
    default_location = os.path.join(os.path.expanduser('~'), "exawind")

    #: Git repo for exawind-builder
    exw_bld_repo = "https://github.com/exawind/exawind-builder.git"

    #: Spack repo
    spack_repo = "https://github.com/spack/spack.git"

    def __init__(self, args=None):
        """Initialize"""
        self.parser = argparse.ArgumentParser(
            description=self.description)
        self.cli_options()
        if args is None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(args)

    def cli_options(self):
        """Command options"""
        parser = self.parser
        parser.add_argument(
            '-p', '--path',
            default=os.getenv('EXAWIND_PROJECT_DIR', self.default_location),
            help="Directory where exawind project is installed")
        parser.add_argument(
            '-s', '--system', default='spack',
            help="System profile to configure")

    def __call__(self):
        self.init_project()
        self.check_system()
        self.setup_spack()

    def init_project(self):
        """Create a skeleton directory structure and fetch exawind-builder"""
        prjdir = abspath(self.args.path)
        if os.path.exists(prjdir):
            print("==> Reusing existing project dir: %s"%prjdir)
        else:
            print("==> Creating ExaWind project structure in %s"%prjdir)

        for pp in "install scripts source".split():
            ensure_directory(os.path.join(prjdir, pp))

        if not os.path.exists(os.path.join(prjdir, "exawind-builder", ".git")):
            success = clone_repo(self.exw_bld_repo, prjdir)
            if not success:
                print("==> ERROR: Cannot clone exawind-builder")
                self.parser.exit(1)
        else:
            print("==> Found exawind-builder in %s"%prjdir)

        self.exawind_dir = prjdir
        self.exw_builder_dir = os.path.join(prjdir, "exawind-builder")

    def check_system(self):
        """Check that the system is a valid system"""
        exw_sys = self.args.system

        with working_directory(os.path.join(self.exw_builder_dir, 'envs')):
            files = glob.glob('*.bash')
            systems = [os.path.splitext(ff)[0] for ff in files]
            if not exw_sys in systems:
                print("==> ERROR: Unknown system requested: %s. Valid options are"%exw_sys)
                for esys in sorted(systems):
                    print("    - %s"%esys)
                self.parser.exit(1)
        self.exw_system = exw_sys

    def setup_spack(self):
        """Clone the spack repository"""
        # User has provided a valid spack repo
        spack_path = os.getenv('SPACK_ROOT')
        valid_spack = (spack_path and
                       os.path.exists(spack_path + '/share/spack/setup-env.sh'))
        if valid_spack:
            print("==> Using spack from SPACK_ROOT: %s"%spack_path)
            self.spack_dir = spack_path
            return

        # Spack directory exists from a previous clone
        spack_path = os.path.join(self.exawind_dir, 'spack')
        if not os.path.exists(spack_path):
            success = clone_repo(self.spack_repo, self.exawind_dir)
            if not success:
                print("==> ERROR: Cannot clone spack")
                self.parser.exit(1)
        else:
            print("==> Reusing spack instance: %s"%spack_path)
            self.spack_dir = spack_path
            return

        print("==> Setting up spack environment")
        ensure_directory(spack_path + "/etc/spack/" + sys.platform)

        cfg_files = "config compilers packages".split()
        src_base = os.path.join(self.exw_builder_dir, "etc/spack/spack")
        dst_base = os.path.join(spack_path, "etc/spack")

        os.symlink(os.path.join(src_base, "repos.yaml"),
                   os.path.join(dst_base, "repos.yaml"))

        for ff in cfg_files:
            fpath = os.path.join(src_base, ff + ".yaml")
            if os.path.exists(fpath):
                os.symlink(fpath, os.path.join(dst_base, ff + ".yaml"))

        sname = 'osx' if sys.platform == 'darwin' else self.exw_system
        cfg_src = os.path.join(self.exw_builder_dir, "etc/spack", sname)
        cfg_dst = os.path.join(spack_path, "etc/spack", sys.platform)
        for ff in cfg_files:
            fpath = os.path.join(cfg_src, ff + ".yaml")
            if os.path.exists(fpath):
                os.symlink(fpath, os.path.join(cfg_dst, ff + ".yaml"))

        have_compilers = any(
            os.path.exists(os.path.join(dd, "compilers.yaml"))
            for dd in [dst_base, cfg_dst])

        if not have_compilers:
            spack_exe = os.path.join(spack_path, "bin/spack")
            subprocess.call([spack_exe, 'compiler', 'find'])

        self.spack_dir = spack_path

if __name__ == "__main__":
    boot = Bootstrap()
    boot()
