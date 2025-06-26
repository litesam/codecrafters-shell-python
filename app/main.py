import os
import shlex
import subprocess
import shutil
from typing import Tuple, List
import readline

def complete_builtin(text, state):
    builtins = ['echo', 'exit']
    matches = []
    for cmd in builtins:
        if cmd.startswith(text):
            matches.append(cmd+' ')
    if state < len(matches):
        return matches[state]
    return None

def setup_readline():
    readline.set_completer(complete_builtin)
    readline.parse_and_bind('tab: complete')
    readline.set_completer_delims(' \t\n`!@#$%^&*()=+[{]}\\|;:\'",<>?')
    readline.set_completion_display_matches_hook(None)

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
        path = args.strip()

        if path == "~":
            path = os.environ.get("HOME", "")

        if not path:
            return

        try:
            os.chdir(path)
        except FileNotFoundError:
            print(f"cd: {args}: No such file or directory", file=os.sys.stderr)
        except Exception as e:
            print(f"cd: {args}: {e}", file=os.sys.stderr)

    def __str__(self):
        return "cd: a shell builtin that changes the current directory"


class TypeExplain(BuiltIn):
    def execute(self, args: str = ""):
        if not args:
            print("type: usage: type [name ...]")
            return

        for token in shlex.split(args):
            if token in ['exit', 'pwd', 'cd', 'type', 'echo']:
                print(token, 'is a shell builtin')
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
    # "echo": Echo,
    "pwd": PWD,
    "cd": CD,
    "type": TypeExplain,
}


def parse_input(input_str: str) -> Tuple[str, str, List[str]]:
    tokens = shlex.split(input_str, posix=True)
    command = tokens[0] if tokens else ""
    args = " ".join(tokens[1:])
    return command, args, tokens

def run_external_command(input_str: str):
    # Detect and handle output redirection
    stdout_file = None
    stderr_file = None
    stdout_append = False
    stderr_append = False
    
    # Check for stderr redirection (2>> or 2>)
    if "2>>" in input_str:
        parts = input_str.split("2>>")
        cmd_part = parts[0].strip()
        stderr_file = parts[1].strip() if len(parts) > 1 else ""
        stderr_append = True
        input_str = cmd_part  # Continue processing for potential stdout redirection
    elif "2>" in input_str:
        parts = input_str.split("2>")
        cmd_part = parts[0].strip()
        stderr_file = parts[1].strip() if len(parts) > 1 else ""
        stderr_append = False
        input_str = cmd_part  # Continue processing for potential stdout redirection
    
    # Check for stdout redirection (1>> or 1> or >> or >)
    if "1>>" in input_str:
        parts = input_str.split("1>>")
        cmd_part = parts[0].strip()
        stdout_file = parts[1].strip() if len(parts) > 1 else ""
        stdout_append = True
    elif "1>" in input_str:
        parts = input_str.split("1>")
        cmd_part = parts[0].strip()
        stdout_file = parts[1].strip() if len(parts) > 1 else ""
        stdout_append = False
    elif ">>" in input_str:
        parts = input_str.split(">>")
        cmd_part = parts[0].strip()
        stdout_file = parts[1].strip() if len(parts) > 1 else ""
        stdout_append = True
    elif ">" in input_str:
        parts = input_str.split(">")
        cmd_part = parts[0].strip()
        stdout_file = parts[1].strip() if len(parts) > 1 else ""
        stdout_append = False
    else:
        cmd_part = input_str
    
    # Parse the command part
    command, args, tokens = parse_input(cmd_part)
    if not command:
        return
    
    path = shutil.which(command)
    if not path:
        print(f"{command}: command not found")
        return
    
    try:
        # Handle file redirections
        stdout_handle = None
        stderr_handle = None
        
        if stdout_file:
            stdout_handle = open(stdout_file, "a" if stdout_append else "w")
        if stderr_file:
            stderr_handle = open(stderr_file, "a" if stderr_append else "w")
        
        # Run the command with appropriate redirections
        subprocess.run(tokens, 
                      stdout=stdout_handle if stdout_handle else None,
                      stderr=stderr_handle if stderr_handle else None)
        
        # Close file handles
        if stdout_handle:
            stdout_handle.close()
        if stderr_handle:
            stderr_handle.close()
            
    except Exception as e:
        print(f"Error: {e}")

# Shell loop
if __name__ == '__main__':
    setup_readline()
    while True:
        try:
            input_str = input("$ ").strip()
            if not input_str:
                continue
            [command, args, tokens] = parse_input(input_str)
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
