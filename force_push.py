import subprocess
import os

def run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except Exception as e:
        return str(e)

log = []

# Clean lock
lock_path = os.path.join('.git', 'index.lock')
if os.path.exists(lock_path):
    os.remove(lock_path)
    log.append('Removed index.lock')

log.append('Adding files...')
log.append(run(['git', 'add', '-A']))

log.append('Committing...')
log.append(run(['git', 'commit', '-m', 'feat: upgrade to gemini-2.0-flash and unify/streamline feedback']))

log.append('Pushing...')
# Use wait to allow network
log.append(run(['git', 'push', 'origin', 'main']))

with open('git_push_log.txt', 'w') as f:
    f.write('\n'.join(log))
