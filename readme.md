

# RS_INSTALL


A package to help install Redesign Science's toolkit
 
## Mac

Pre-requisites:

  - make sure you have access to the R_S github repo

Go to the directory in which you want to store the packages.  

Try this first:
  
    python3 -c "$(curl -fsSL https://raw.githubusercontent.com/RedesignScience/rs_install/main/rs_install_mac.py)"
    
    
Otherwise, save <a download href="https://raw.githubusercontent.com/RedesignScience/rs_install/main/rs_install_mac.py">rs_install_mac.py</a>. then run:

    python3 rs_install_mac.py

If you need to install Conda, once the script has installed Conda, it will stop
to let you start Conda by reopening the terminal.

Go back to the script, and run it to continue from where you left off.


## Todo
- User credentials
  - need AWS access
  - kubectl
  - argo
  - need config files for HSDS
  - need config files for db
  - need OpenEye license
