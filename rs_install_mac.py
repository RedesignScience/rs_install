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
        print(f"Check binary: {binary} installed")
    else:
        print("Installing {binary}")
        run(install_cmd)


def header_print(s):
    print()
    print(">" * 70)
    for line in s.splitlines():
        print(f"> {line}")
    print(">" * 70)


if len(sys.argv) > 1:
    env = sys.argv[1]
else:
    env = 'rs'


if len(sys.argv) > 2:
    package_dir = Path(sys.argv[1])
else:
    package_dir = Path(env)

package_dir.mkdir(exist_ok=True)

header_print(f"""\
Setting up `{env}` conda environment in {package_dir.resolve()}
(optional: python3 rs_install_mac.py <env_name> <package_dir>)""")

os.chdir(package_dir)

header_print(f"Checking unix utilities")
install_cmd(
    "brew",
    f'/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
)
install_cmd("wget", f"brew install wget")


if not shutil.which("conda"):
    header_print(f"Install Conda")

    # Must use x86 and rely on Rosetta
    fname = "Miniconda3-latest-MacOSX-x86_64.sh"
    if not Path(fname).exists():
        run(f"wget https://repo.anaconda.com/miniconda/{fname} -O {fname}")
    run(f"bash ./{fname} -u")

    print("")
    print("Hopefully you've installed conda.")
    print("Now you need to restart the terminal to trigger conda.")
    print("")
    print("Restart the terminal and then come back to this directory.")
    print("Then restart the script and it will continue the installation.")
    sys.exit(1)


header_print(f"Checking `{env}` conda environment")
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


header_print("Connect to R_S github website")

install_cmd("gh", f"brew install gh")
run("gh auth login")
install_cmd("git", f"brew install git")


package = "rs_install"
header_print(f"R_S Package: {package}")

if not Path(package).exists():
    run(f"gh repo clone RedesignScience/{package}")

os.chdir(package)
run("git pull")
os.chdir('..')


header_print("Conda install for special packages")

install_cmd("mamba", "conda install -y mamba")

run(f"mamba env update -n {env} -f rs_install/rs_mac_conda_env.yaml")



pip = f"{env_path}/bin/pip"

packages = []
for line in open("rs_install/packages.yaml"):
    tokens = line.split()
    if len(tokens) and tokens[0] == "-":
        package = tokens[1]
        header_print(f"R_S Package: {package}")

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


header_print(f"Installation Complete")

print(f"""

Hopefully the R_S packages have been installed in the directory
    
    {Path(".").resolve()}

To access the packages in the `{env}` conda environment.

    > conda activate {env}
    
Check if `rseed` is available (you might have to wait for the Rosetta
conversion x86 -> ARM to kick in):

    > rseed
    
Then open up a trajectory from foamdb:

    > rshow traj-foam 23    

""")



