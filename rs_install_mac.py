#!/usr/bin/env python3

import subprocess
import shutil
from pathlib import Path
import os
import sys


def run(cmds):
    result = None
    for cmd in cmds.splitlines():
        if cmd:
            print()
            print(">", cmd.lstrip())
            result = subprocess.run(cmd, shell=True)
    return result


def get_output_of_run(cmd):
    bytes = subprocess.check_output(cmd.split())
    text = bytes.decode("utf-8", errors="ignore")
    return text


def install_cmd(binary, install_cmd):
    if shutil.which(binary):
        print(f"Checking for {binary}: installed")
    else:
        print("Installing {binary}")
        run(install_cmd)


def print_header(s):
    print()
    print(">" * 70)
    for line in s.splitlines():
        print(f">   {line}")
    print(">" * 70)



args = sys.argv[1:]
env = 'rs' if not len(args) else args[0]
top_dir = Path(env) if len(args) <= 1 else Path(args[1])


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
    run(f"conda create -n {env} -y python=3.8")
text = get_output_of_run("conda env list")
for line in text.splitlines():
    tokens = line.split()
    if env in tokens:
        env_path = tokens[-1]
        print(f"Location of `{env}` environment: {env_path}")
        break
else:
    print(f"Error: can't find `{env}` conda environment")
    sys.exit(1)


# Connect to github.com/RedesignScience
print_header("Connect to R_S github website")
install_cmd("gh", f"brew install gh")
run("gh auth login")
install_cmd("git", f"brew install git")


# Checking for R_S package directory
print_header(f"Checking R_S packages in {top_dir.resolve()}")
top_dir.mkdir(exist_ok=True)
os.chdir(top_dir)


# Download rs_install as it has package lists and env.yamls
package = "rs_install"
print_header(f"R_S package: {package}")
if not Path(package).exists():
    run(f"gh repo clone RedesignScience/{package}")
os.chdir(package)
run("git pull")
os.chdir('..')


# Check for special Conda downloads 
print_header("Conda install for special packages")
install_cmd("mamba", "conda install -y mamba")
run(f"mamba env update -n {env} -f rs_install/rs_mac_conda_env.yaml")


# Download R_S packages
pip = f"{env_path}/bin/pip"
for line in open("rs_install/packages.yaml"):
    tokens = line.split()
    if len(tokens) and tokens[0] == "-":
        package = tokens[1]
        print_header(f"R_S package: {package}")
        if not Path(package).exists():
            run(f"gh repo clone RedesignScience/{package}")
        os.chdir(package)
        run(f"git pull")
        if package == "foamdb":
            run(f"{pip} install sqlalchemy alembic psycopg2-binary")
            run(f"{pip} install .")
        else:
            run(f"{pip} install -e .")
        os.chdir('..')


# Final instructions
print_header(f"Installation Complete")
print(f"""

The R_S packages should be in the directory
    
    {Path(".").resolve()}

To access the packages in the `{env}` conda environment.

    > conda activate {env}
    
Check if `rseed` is available (you might have to wait for the Rosetta
conversion x86 -> ARM to kick in):

    ({env})> rseed
    
Then open up a trajectory from foamdb:

    ({env})> rshow traj-foam 23    

""")



