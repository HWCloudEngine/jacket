import sys
from sys import platform as _platform
import subprocess
import os.path
import shutil
# import nova
# import cinder
import pkgutil
import time
import glob
import errno

def _salf_copy(src_path, dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy2(src_path,dst_dir)

def _backup_file(org_file_path, backup_dir_path):
    try:
        backup_file_dst_dir = os.path.dirname(os.path.join(backup_dir_path,
                                                           os.path.relpath(org_file_path,SITE_DIR)))
        _salf_copy(org_file_path, backup_file_dst_dir)
    except IOError as e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise e

def _backup_files_all(org_file_path_list, backup_dir_path):
    for org_file_path in org_file_path_list:
        _backup_file(org_file_path, backup_dir_path)


def _restore_files_all(backup_dir,installed_base_dir):
    for b,d,fs in os.walk(backup_dir):
        for f in fs:
            shutil.move(os.path.join(b,f),
                        os.path.join(installed_base_dir,os.path.relpath(b,backup_dir),f))

#todo: install & backup project
# python jacket.py install -r record_file_name
# -r:  record_file_name
# -p:  customized parameters, key=value
def _func_install(*params):

    print("Installing: Start to install jacket...")
    # copy projects
    if os.path.exists(PROJECT_DIR):
        shutil.rmtree(PROJECT_DIR)

    # mv .egg-info to site-packages
    print("Installing: copy egg to site-packages")
    try:
        shutil.copytree(EGG_NAME,EGG_DIR)
    except Exception as e:
        shutil.rmtree(EGG_DIR)
        shutil.copytree(EGG_NAME,EGG_DIR)

    with open(INSTALLED_LOG,"a+") as f:

        # backup and copy drivers
        print("Installing: copy drivers")

        for li in DRIVER_MANIFEST:
            orig_file_path = os.path.join(SITE_DIR,li)
            if os.path.exists(orig_file_path):
                # backup
                _backup_file(orig_file_path, BACKUP_DIR)

            # copy driver files
            try:
                installed_path = os.path.join(SITE_DIR,li);
                _salf_copy(li,os.path.dirname(installed_path))
                f.write(installed_path+"\n")
            except:
                _func_uninstall()
                pass



        for li in PROJECT_MANIFEST:
            try:
                installed_path = os.path.join(PROJECT_DIR,li);
                _salf_copy(li,os.path.dirname(installed_path))
                f.write(installed_path+"\n")
            except:
                _func_uninstall()
                pass

        # backup and install pathes



    print("Installing: Successfully installed jacket")

# def _func_install(params):
#
#     print("Start to install jacket...")
#
#
#     cmd_dir = os.path.dirname(os.path.abspath(__file__))
#
#     setup_py_dir = os.path.dirname(cmd_dir)
#     # setup_py_path = os.path.join("setup.py")
#     os.chdir(setup_py_dir)
#
#     # buackup and copy drivers
#     for path in driver_dirs:
#         if os.path.exists(path):
#             shutil.move(path, ".".join([path,"bak","jacket"]))
#
#
#     # install
#     if os.path.isfile("setup.py"):
#
#             cmd_setup_install = " ".join(["python","setup.py","install","--record installed.txt"])
#
#             if _platform == "linux" or _platform == "linux2":
#                 # TERMINAL_PATH = "/bin/sh"
#                 ret = subprocess.call(cmd_setup_install,shell=True)
#             elif _platform == "win32":
#                 TERMINAL_PATH = "C:\Program Files\Git\git-bash.exe"
#                 ret = subprocess.call([TERMINAL_PATH,"-c",cmd_setup_install],shell=True)
#
#             # terminal_git = subprocess.Popen(terminal_git_path,
#             #                                 shell=True,
#             #                                 stdin=subprocess.PIPE,
#             #                                 stdout=subprocess.PIPE)
#             # ret = terminal_git.communicate(cmd_setup_install.encode('utf-8'))
#             # terminal_git.wait()
#
#     else:
#         raise Exception('Can NOT find setup.py')




#todo: uninstall & rollback project
# python jacket.py uninstall -r record_file_name
# -r:  record_file_name
# -p:  customized parameters, key=value
def _func_uninstall(*params):

    # if os.path.isfile(installed_record):
    #     subprocess.call([TERMINAL_PATH,"-c","cat",installed_record,"| xarg rm -rf"],shell=True)

    print("Uninstalling: Start to uninstall jacket...")

    # delete installed files
    print("Uninstalling: delete installed files")
    installed_dirs = []
    with open(INSTALLED_LOG) as f:
        for li in f:
            path = li.strip()
            try:
                installed_dirs.append(os.path.dirname(path))
                os.remove(path)
                if os.path.exists(path + "c"):
                    os.remove(path + "c") # remove *.pyc
            except Exception as e:
                print(e)
                if os.path.exists(path + "c"):
                    os.remove(path + "c") # remove *.pyc
                pass

    # restore
    print("Uninstalling: restore...")
    _restore_files_all(BACKUP_DIR,SITE_DIR)

    for dir in set(installed_dirs):
        try:
            os.rmdir(dir)
        except:
            pass

    # delete egg
    print("Uninstalling: delete egg")
    try:
        shutil.rmtree(EGG_DIR)
    except Exception as e:
        print(e)

    print("Uninstalling: delete project directories")
    try:
        shutil.rmtree(PROJECT_DIR)
    except Exception as e:
        print(e)


    print("Uninstalling: Successfully uninstall jacket")

#todo: start service:
# python jacket.py start
# current status: support linux installed cps only
def _func_start(*params):
    pass

#todo: stop service:
# python jacket.py stop
def _func_stop(*params):
    pass

#todo: restart service:
# python jacket.py restart
def _func_restart(params):
    if 0!=subprocess.call("cps host-template-instance-operate --action stop --service cinder cinder-volume",shell=True) :
        raise Exception("Stop cinder volume service failed")
    time.sleep(1)

    if 0!=subprocess.call("cps host-template-instance-operate --action start --service cinder cinder-volume",shell=True):
        raise Exception("Start cinder volume service failed")

    if 0!=subprocess.call("cps host-template-instance-operate --action stop --service nova nova-compute",shell=True):
        raise Exception("Stop nova compute service failed")

    time.sleep(1)
    if 0!=subprocess.call("cps host-template-instance-operate --action start --service nova nova-compute",shell=True):
        raise Exception("Stop nova compute service failed")

COMMAND_DICT = {
    'install': _func_install,
    'uninstall': _func_uninstall,
    'start': _func_start,
    'stop': _func_stop,
    'restart': _func_restart
}

PROJECT_NAME = "jacket"
NOVA_DIR = pkgutil.get_loader("nova").filename
CINDER_DIR = pkgutil.get_loader("cinder").filename
SITE_DIR = os.path.dirname(NOVA_DIR)
EGG_NAME = "%s.egg-info" % PROJECT_NAME
EGG_DIR = os.path.join(SITE_DIR,EGG_NAME)
PROJECT_DIR = os.path.join(SITE_DIR,PROJECT_NAME)
BACKUP_DIR = os.path.join(PROJECT_DIR,"backup")
INSTALLED_LOG = os.path.join(EGG_DIR,"installed.txt")
DRIVER_MANIFEST = []
PROJECT_MANIFEST = []
PATCH_MANIFEST = []

if __name__ == '__main__':

    # parse params
    subcommand = sys.argv[1]
    params = sys.argv[2:]

    this_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(this_dir)

    with open(os.path.join(this_dir,EGG_NAME,"SOURCES.txt")) as f:
        DRIVER_MANIFEST = []
        for line in f.readlines():
            if line.startswith("nova") or line.startswith("cinder"):
                DRIVER_MANIFEST.append(line.strip())
            elif line.startswith("patches"):
                PATCH_MANIFEST.append(line.strip("patches"))
            else:
                PROJECT_MANIFEST.append(line.strip())

    PROJECT_MANIFEST.remove("setup.py")
    PROJECT_MANIFEST.remove("setup.cfg")



    # driver_dirs = [os.path.join(nova_path,"virt","aws"),
    #                os.path.join(nova_path,"virt","vcloudapi"),
    #                os.path.join(nova_path,"virt","vmwareapi"),
    #                os.path.join(nova_path,"virt","vtep"),
    #                os.path.join(cinder_path,"volume","drivers","ec2"),
    #                os.path.join(cinder_path,"volume","drivers","vcloud"),
    #                os.path.join(cinder_path,"volume","drivers","vmware")]

    func_cmd = COMMAND_DICT[subcommand]

    try:
        sys.exit(func_cmd(params))
    except Exception as e:
        # do someting here
        raise e