Import("env")
import shutil
import os
import subprocess

node_ex = shutil.which("node")
# Check if Node.js is installed and present in PATH if it failed, abort the build
if node_ex is None:
    print('\x1b[0;31;43m' + 'Node.js is not installed or missing from PATH html css js will not be processed check https://kno.wled.ge/advanced/compiling-wled/' + '\x1b[0m')
    exitCode = env.Execute("null")
    exit(exitCode)
else:
    # Check if node_modules exists and has the required packages
    need_npm_install = False
    if not os.path.exists("node_modules"):
        need_npm_install = True
    elif not os.path.exists("node_modules/web-resource-inliner"):
        need_npm_install = True
    elif not os.path.exists("node_modules/html-minifier-terser"):
        need_npm_install = True
    
    # Only install packages if needed
    if need_npm_install:
        print('\x1b[6;33;42m' + 'Installing node packages' + '\x1b[0m')
        env.Execute("npm ci")
    else:
        print('\x1b[6;37;42m' + 'Node packages already installed, skipping npm ci' + '\x1b[0m')

    # Call the bundling script (it has its own smart rebuild detection)
    exitCode = env.Execute("npm run build")

    # If it failed, abort the build
    if (exitCode):
      print('\x1b[0;31;43m' + 'npm run build fails check https://kno.wled.ge/advanced/compiling-wled/' + '\x1b[0m')
      exit(exitCode)
