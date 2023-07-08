import os
import subprocess

# Create and activate the virtual environment
venv_dir = os.path.join(os.getcwd(), 'venv')
subprocess.run(['python', '-m', 'venv', venv_dir])
os_name = os.name
if os_name == 'nt':  # For Windows
    activate_cmd = os.path.join(venv_dir, 'Scripts', 'activate.bat')
    subprocess.run([activate_cmd], shell=True)
else:
    activate_cmd = os.path.join(venv_dir, 'bin', 'activate')
    subprocess.run(['source', activate_cmd], shell=True)

# Install required packages
subprocess.run(['pip', 'install', '-r', 'meta/requirements.txt'])