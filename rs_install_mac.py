#!/usr/bin/env python3

import subprocess
import shutil
from pathlib import Path
import os
import sys
import stat


def run(cmds):
    result = None
    for cmd in cmds.splitlines():
        if cmd:
            print()
            print(">", cmd.lstrip())
            result = subprocess.run(cmd, shell=True)
    return result


def get_lines_of_run(cmd):
    bytes = subprocess.check_output(cmd.split())
    text = bytes.decode("utf-8", errors="ignore")
    return text.splitlines()


def install_cmd(binary, install_cmd):
    if shutil.which(binary):
        print(f"Checking for {binary}: installed")
    else:
        print("Installing {binary}")
        run(install_cmd)


def print_header(s):
    print()
    print()
    print(">" * 70)
    for line in s.splitlines():
        print(f">   {line}")
    print(">" * 70)


def get_home():
    return  Path(os.path.expanduser("~"))


def dirty_read_toml(fname):
    result = {}
    for line in open(fname):
        if "=" in (tokens := line.split()):
            result[tokens[0]] = tokens[2]
    return result


def check_aws_configure():
    fname = get_home() / ".aws" / "credentials"
    if not fname.exists():
        return False
    credentials = dirty_read_toml(fname)
    if "aws_access_key_id" not in credentials:
        return False
    if "aws_secret_access_key" not in credentials:
        return False
    fname = get_home() / ".aws" / "config"
    if not fname.exists():
        return False
    config = dirty_read_toml(fname)
    if "region" not in config:
        return False
    if config["region"] != "us-east-1":
        return False
    return True


def check_config_file(fname, basename, url):
    if Path(fname).exists():
        print(f"Check `{fname}`: exists")
    else:
        print(f"Missing config: `{Path(fname).name}`")
        print(f"Please download: `{basename}`")
        print(f"From: {url}")
        print(f"And copy to: `{fname}`")


args = sys.argv[1:]
env = 'rs' if not len(args) else args[0]
top_dir = Path(env) if len(args) <= 1 else Path(args[1])
python_version = "3.8"


# Greeting message
print_header(f"""rs_install """)
print(f"""
Install/Update the R_S Toolkit on your Mac.

R_S package directory: {top_dir.resolve()}
Python conda environment: `{env}` 

(optional: python3 rs_install_mac.py <env_name> <top_dir>)
""")


# Check for standard unix utilities
print_header(f"Checking unix utilities")
install_cmd(
    "brew",
    f'/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
)
install_cmd("wget", f"brew install wget")
install_cmd("kubectl", f"brew install kubectl")
install_cmd("argo", f"brew install argo")
install_cmd("aws", f"brew install awscli")


# Check for Conda install
if not shutil.which("conda"):
    print_header(f"Install Conda - must be the x86 and not ARM version")
    # Must use x86 and rely on Rosetta
    fname = "Miniconda3-latest-MacOSX-x86_64.sh"
    if not Path(fname).exists():
        run(f"wget https://repo.anaconda.com/miniconda/{fname} -O {fname}")
    run(f"bash ./{fname} -u")
    if not shutil.which("conda"):
        print("")
        print("Hopefully you've installed conda.")
        print("Now you need to restart the terminal to trigger conda.")
        print("")
        print("Restart the terminal and then come back to this directory.")
        print("Then restart the script and it will continue the installation.")
        sys.exit(1)


# Check if our Conda environment has been created
print_header(f"Checking `{env}` conda environment")
if run(f"conda env list | grep {env}").returncode != 0:
    run(f"conda create -n {env} -y python={python_version}")
for line in get_lines_of_run("conda env list"):
    if env in (tokens := line.split()):
        env_path = tokens[-1]
        print(f"Location of `{env}` environment: {env_path}")
        break
else:
    print(f"Error: can't find `{env}` conda environment")
    sys.exit(1)


# Connect to github.com/RedesignScience
print_header("Connect to R_S github website")
install_cmd("gh", f"brew install gh")
if run("gh repo list > /dev/null").returncode != 0:
    run("gh auth login")
else:
    print("You are logged-in to gh")


# Checking for R_S package directory
print_header(f"Checking R_S packages in {top_dir.resolve()}")
top_dir.mkdir(exist_ok=True)
os.chdir(top_dir)


# Create install.sh
sh = "install.sh"
open(sh, "w").write(f"./rs_install/rs_install_mac.py {env} {top_dir.resolve()}")
st = os.stat(sh)
os.chmod(sh, st.st_mode | stat.S_IEXEC)
print(f"Created {sh}")


# Download rs_install as it has package lists and env.yamls
package = "rs_install"
print_header(f"R_S package: {package}")
if not Path(package).exists():
    run(f"gh repo clone RedesignScience/{package}")
os.chdir(package)
run("gh repo sync")
os.chdir('..')


# Check for special Conda downloads
print_header("Conda install for precompiled binaries")
install_cmd("mamba", "conda install -y mamba")
run(f"mamba env update -n {env} -f rs_install/mac_env.yaml")


# Download R_S packages
pip = f"{env_path}/bin/pip"
for line in open("rs_install/packages.yaml"):
    tokens = line.split()
    if not len(tokens) or tokens[0] != "-":
        continue
    package = tokens[1]
    print_header(f"R_S package: {package}")
    if not Path(package).exists():
        run(f"gh repo clone RedesignScience/{package}")
    os.chdir(package)
    run(f"gh repo sync")
    if package == "foamdb":
        run(f"{pip} install sqlalchemy alembic psycopg2-binary")
        run(f"{pip} install .")
    else:
        run(f"{pip} install -e .")
    os.chdir('..')


# Checking config file for tools that access our distributed platforms


# Check AWS is configured
print_header(f"Check AWS config: for launching remote jobs")
if check_aws_configure():
    print(f"AWS looks to be configured correctly")
else:
    print(f"")
    print(f"You need to configure AWS with your credentials provided by our dev ops")
    print(f"  - AWS Access Key ID: ?")
    print(f"  - AWS Secret Access Key: ?")
    print(f"  - region: us-east-1")
    run("aws configure")


# Check kubernetes to allow argo list
print_header("Checking OpenEye license: for ligand analysis in rseed")
check_config_file(
    top_dir / "rseed/license/oe_license.txt",
    "oe_license.txt",
    "https://www.notion.so/redesignscience/RSeed-f0df0212bba6469db3d5e774c99c87d0#307c435748364d19ba84e03d7123b667"
)


# Check kubernetes to allow argo list
print_header("Checking Kubernetes config: for monitoring remote jobs")
check_config_file(
    get_home() / ".kube/config",
    "cw-kubeconfig.txt",
    "https://www.notion.so/redesignscience/Using-RSCloud-with-Orion-dd12c4c6e1d3473ab44678e0a05461b8#af8e52a7fcd14b298a1d7b081fae72b1"
)

# Check FoamDB to allow upload/downloand/viewing of trajectories
print_header("Checking FoamDB config: for upload/download to traj database")
check_config_file(
    get_home() / ".config/foamdb/config.json",
    "config.json",
    "https://www.notion.so/redesignscience/Credentials-55cd7fdaae764d699b1766ceafdd4dc9#74256ba09c404df899117022b225359d"
)
check_config_file(
    get_home() / ".hscfg",
    ".hscfg",
    "https://www.notion.so/redesignscience/Credentials-55cd7fdaae764d699b1766ceafdd4dc9#257f20440928466a862d225bb45405c6"
)


# Final instructions
print_header(f"Installation Complete")
print(f"""

The R_S packages should be in the directory
    
    {Path(".").resolve()}

To access the packages in the `{env}` conda environment.
d
    > conda activate {env}
    
Check if `rseed` is available (you might have to wait for the Rosetta
conversion x86 -> ARM to kick in):

    ({env})> rseed
    
Then open up a trajectory from foamdb:

    ({env})> rshow traj-foam 23    

""")



