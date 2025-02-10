import sys

from pydantic import ValidationError
from pydantic_settings import CliApp, SettingsError

from issue_solver.standalone.ReviewCommand import ReviewSettings
from issue_solver.standalone.SolveCommand import SolveCommand


class CuduCLI:
    @classmethod
    def run(
        cls,
    ) -> None:
        if len(sys.argv) < 2:
            show_usage()
            sys.exit(1)

        subcmd = sys.argv[1]
        sub_args = sys.argv[2:]
        try:
            if subcmd == "solve":
                CliApp.run(
                    model_cls=SolveCommand,
                    cli_args=sub_args,  # le reste des arguments
                    cli_cmd_method_name="cli_cmd",
                )
            elif subcmd == "review":
                CliApp.run(
                    model_cls=ReviewSettings,
                    cli_args=sub_args,
                    cli_cmd_method_name="cli_cmd",
                )
            elif subcmd in ("help", "-h", "--help"):
                show_usage()
                sys.exit(0)
            else:
                print(f"Unknown subcommand: {subcmd}")
                show_usage()
                sys.exit(1)
        except ValidationError as e:
            print("[ERROR] Invalid arguments or fields:\n")
            errors = e.errors()
            for err in errors:
                print(f" - {err['loc']}: {err['msg']} | input: {err['input']}")
            sys.exit(2)

        except SettingsError as e:
            print("[ERROR] Bad configuration or CLI usage:\n")
            print(e)
            sys.exit(2)


def show_usage() -> None:
    """Show general help for the `cudu` CLI."""
    print("""
    Usage: cudu [subcommand] [options...]
    Subcommands:
      solve    🧩 solve an issue
      review   👀 review a pull request or issue
      help     🛟 show this message
    
    Examples:
      cudu solve --repo-path=. --agent=swe-crafter
      cudu review --repo-path=.
      cudu solve --help       # show help about the 'solve' subcommand
    """)
