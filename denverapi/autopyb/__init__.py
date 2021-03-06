import argparse
import functools
import sys
import textwrap

from .commands import *

try:
    from .. import colored_text
except ImportError:
    import denverapi.colored_text

print = colored_text.print
input = colored_text.input

__version__ = "1.1.0"


# noinspection PyCallByClass
class BuildTasks:
    def __init__(self):
        self.ignored_tasks = []
        self.accomplished = []
        self.tasks = []

    def task(self, *dependencies, forced=False, ignored=False, uses_commandline=False):
        def decorator(function):
            @functools.wraps(function)
            def wrapper_function(arguments=None):
                if arguments is None:
                    arguments = []
                print(f"-------------{function.__name__}-------------", fore="green")
                for depend in dependencies:
                    is_list = False
                    if callable(depend):
                        x = depend
                    elif isinstance(depend, (tuple, list)):
                        x = depend[0]
                        is_list = True
                    else:
                        raise TypeError(
                            "dependencies must be a function or a tuple[function: callable, [...]]"
                        )
                    if x not in self.accomplished:
                        print(
                            f"Running Task {x.__name__} (from {function.__name__})",
                            fore="magenta",
                        )
                        if x not in self.ignored_tasks:
                            self.accomplished.append(x)
                        try:
                            if is_list:
                                x(depend[1])
                            else:
                                x(None)
                        except Exception as e:
                            print(
                                f"Encountered {e.__class__.__name__}: {str(e)} ({x.__name__})",
                                fore="red",
                            )
                            sys.exit(1)
                    else:
                        print(
                            f"Skipped Task {x.__name__} (from {function.__name__})",
                            fore="cyan",
                        )
                if uses_commandline:
                    function(arguments)
                else:
                    function()
                print(
                    colored_text.escape(
                        f"{{fore_green}}----{{back_red}}{{fore_yellow}}end{{reset_all}}{{style_bright}}{{fore_green}}"
                        + f"------{function.__name__}-------------"
                    )
                )

            if forced:
                self.ignored_tasks.append(wrapper_function)

            if not ignored:
                self.tasks.append(wrapper_function)

            return wrapper_function

        return decorator

    def interact(self, arguments=None):
        if arguments is None:
            arguments = sys.argv[1:]
        parser = argparse.ArgumentParser()
        task_list = []
        command = parser.add_subparsers(dest="command_")
        for x in self.tasks:
            task_list.append(x.__name__)
            doc_help = (
                x.__doc__ if x.__doc__ is not None else "Help Not Provided"
            ).strip("\n")
            command.add_parser(x.__name__, help=textwrap.dedent(doc_help))
        args = parser.parse_args(arguments[0:1])
        for x in self.tasks:
            if args.command_ == x.__name__:
                try:
                    x(arguments[1:])
                except KeyboardInterrupt:
                    print("User aborted the process", fore="red")
                    print(
                        colored_text.escape(
                            f"{{fore_green}}----{{back_red}}{{fore_yellow}}end{{reset_all}}{{style_bright}}"
                            f"{{fore_green}} "
                            f"------{x.__name__}-------------"
                        )
                    )
                except Exception as e:
                    print(
                        f"Process Failed with {e.__class__.__name__}: {str(e)}",
                        fore="red",
                    )
                    print(
                        colored_text.escape(
                            f"{{fore_green}}----{{back_red}}{{fore_yellow}}end{{reset_all}}{{style_bright}}{{"
                            "fore_green}" + f"------{x.__name__}-------------"
                        )
                    )
