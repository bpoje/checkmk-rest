import subprocess
import shlex as shl


def bash_no_stdin(cmd: str, merge_stdout_stderr=True) -> subprocess.Popen:
    'Run cmd string in bash, close stdin and wait for execution to finish'

    cmd = shl.split(cmd)

    if merge_stdout_stderr:
        # stderr => stdout, stdout => pipe
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, encoding='utf8')
    else:
        # stderr => pipe, stdout => pipe
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8')

    # Close stdin
    p.stdin.close()

    # Wait till command finishes
    while p.returncode is None:
        p.poll()

    return p
