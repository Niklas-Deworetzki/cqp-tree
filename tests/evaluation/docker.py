import subprocess
from typing import Optional


def docker_run_command(
    image: str,
    command: Optional[str] = None,
    args: list[str] = [],
    mounts: dict[str, str] = {},
    ports: list[int] = [],
    network: Optional[str] = None,
    env: dict[str, str] = {},
    remove: bool = True,
    interactive: bool = True,
    tty: bool = True,
    detach: bool = False,
):
    executable = ['docker', 'run']
    if remove:
        executable.append('--rm')
    if interactive:
        executable.append('--interactive')
    if tty:
        executable.append('--tty')
    if detach:
        executable.append('--detach')
    for source_path, target_path in mounts.items():
        executable.append('--mount')
        executable.append(f'type=bind,source={source_path},target={target_path}')
    for key, value in env.items():
        executable += ['--env', f'{key}={value}']
    if network:
        executable += ['--network', network]
    for port in ports:
        executable += ['--publish', f'{port}:{port}']
    executable.append(image)
    if command:
        executable.append(command)
    executable += args
    return executable


def docker_stop_command(container: str):
    return ['docker', 'stop', container]


def docker_exec_command(container: str, *command: str):
    return ['docker', 'exec', container] + list(command)


class Container:
    def __init__(
        self,
        image: str,
        command: Optional[str] = None,
        args: list[str] = [],
        mounts: dict[str, str] = {},
        ports: list[int] = [],
        network: Optional[str] = None,
        env: dict[str, str] = {},
    ):
        self.start_command = docker_run_command(
            image, command, args, mounts, ports, network, env, detach=True
        )
        self.container_id = None

    def start(self):
        assert self.container_id is None, 'Container already started.'
        exec_result = subprocess.run(self.start_command, capture_output=True)
        if exec_result.returncode:
            print(exec_result.stderr)
            raise ValueError()
        self.container_id = exec_result.stdout.strip()

    def stop(self):
        assert self.container_id is not None, 'Container not running.'
        subprocess.run(docker_stop_command(self.container_id), stdout=subprocess.DEVNULL)
        self.container_id = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.stop()

    def exec(self, *cmd: str) -> str:
        assert self.container_id is not None, 'Container not running.'
        exec_result = subprocess.run(
            docker_exec_command(self.container_id, *cmd),
            capture_output=True,
            text=True,
        )
        if exec_result.returncode != 0:
            raise ValueError('Execution failed: ' + exec_result.stderr)
        return exec_result.stdout
