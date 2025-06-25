import os
import shlex
import subprocess
from typing import Tuple, List


class BuiltIn:
    def execute(self, args: str = ""):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class BuiltinFactory:
    builtins = {}

    @staticmethod
    def create(command: str):
        return BuiltinFactory.builtins.get(command, lambda: None)()

    @staticmethod
    def is_builtin(command: str) -> bool:
        return command in BuiltinFactory.builtins


class Exit(BuiltIn):
    def execute(self, args: str = ""):
        exit(0)

    def __str__(self):
        return "exit is a shell builtin"


class Echo(BuiltIn):
    def execute(self, args: str = ""):
        print(args)

    def __str__(self):
        return "echo is a shell builtin"


class PWD(BuiltIn):
    def execute(self, args: str = ""):
        print(os.getcwd())

    def __str__(self):
        return "pwd is a shell builtin"


class CD(BuiltIn):
    def execute(self, args: str = ""):
        path = args.strip() or os.environ.get("HOME", "")
        if path == "~":
            path = os.environ.get("HOME")
        try:
            os.chdir(path)
        except FileNotFoundError:
            print(f"cd: {path}: No such file or directory", file=os.sys.stderr)
        except Exception as e:
            print(f"cd: {path}: {e}", file=os.sys.stderr)

    def __str__(self):
        return "cd: a shell builtin that changes the current directory"


class TypeExplain(BuiltIn):
    def execute(self, args: str = ""):
        if not args:
            print("type: usage: type [name ...]")
            return

        for token in shlex.split(args):
            if BuiltinFactory.is_builtin(token):
                builtin = BuiltinFactory.create(token)
                print(str(builtin))
            else:
                path = self.find_in_path(token)
                if path:
                    print(f"{token} is {path}")
                else:
                    print(f"{token}: not found")

    def find_in_path(self, cmd: str) -> str:
        for dir in os.environ.get("PATH", "").split(":"):
            full_path = os.path.join(dir, cmd)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return ""

    def __str__(self):
        return "type is a shell builtin"


BuiltinFactory.builtins = {
    "exit": Exit,
    "echo": Echo,
    "pwd": PWD,
    "cd": CD,
    "type": TypeExplain,
}


def parse_input(input_str: str) -> Tuple[str, str, List[str]]:
    tokens = shlex.split(input_str)
    command = tokens[0] if tokens else ""
    args = " ".join(tokens[1:])
    return command, args, tokens


def run_external_command(input_str: str):
    command, args, tokens = parse_input(input_str)

    if not command:
        return

    path = shutil.which(command)
    if not path:
        print(f"{command}: command not found")
        return

    try:
        subprocess.run(tokens)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    import shutil

    while True:
        try:
            input_str = input("$ ").strip()
            if not input_str:
                continue

            command, args, tokens = parse_input(input_str)

            if BuiltinFactory.is_builtin(command):
                builtin = BuiltinFactory.create(command)
                if builtin:
                    builtin.execute(args)
            else:
                run_external_command(input_str)

        except EOFError:
            break
        except KeyboardInterrupt:
            print()

