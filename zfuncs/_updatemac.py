#!/usr/bin/env python3
"""
Update macOS, App Store, and Homebrew in a maintainable, parallelizable way.
Gracefully handles user cancellation (Ctrl+C) and logs a friendly message.
"""
import argparse
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, List

import colorama
from colorama import Fore

# Constants
DEFAULT_LOGFILE = Path.home() / "updatemac_log.txt"


class UpdateTask:
    """
    Represents an update task with a check and update command.
    """
    def __init__(self, name: str, check_cmd: List[str],
                 update_cmd: List[str],
                 check_fn: Callable[[subprocess.CompletedProcess], bool]):
        self.name = name
        self.check_cmd = check_cmd
        self.update_cmd = update_cmd
        self.check_fn = check_fn
        self.pending = False

    def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """
        Executes a command and returns the CompletedProcess.
        """
        logging.debug(f"Running command: {' '.join(cmd)}")
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True)
            logging.debug(f"{cmd} stdout: {cp.stdout.strip()}")
            logging.debug(f"{cmd} stderr: {cp.stderr.strip()}")
            return cp
        except Exception as e:
            logging.exception(f"Error running command {' '.join(cmd)}: {e}")
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))

    def check(self) -> bool:
        """
        Checks if updates are pending.
        """
        logging.info(f"Checking for {self.name} updates...")
        result = self.run_command(self.check_cmd)
        self.pending = self.check_fn(result)
        if self.pending:
            logging.warning(f"{self.name} updates are pending")
        else:
            logging.info(f"No {self.name} updates available")
        return self.pending

    def update(self) -> bool:
        """
        Performs the update if pending.
        """
        logging.info(f"Updating {self.name}...")
        try:
            result = self.run_command(self.update_cmd)
        except KeyboardInterrupt:
            logging.warning(Fore.RED + f"{self.name} update cancelled by user.")
            return False
        if result.returncode == 0:
            logging.info(f"{self.name} update completed successfully")
            return True
        else:
            logging.error(f"{self.name} update failed: {result.stderr.strip()}")
            return False


def check_internet() -> bool:
    """
    Verifies internet connectivity by pinging a reliable server.
    """
    try:
        subprocess.check_call(
            ["ping", "-c", "1", "8.8.8.8"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update macOS, App Store, and Homebrew with graceful cancellation"
    )
    parser.add_argument(
        "--no-interaction",
        action="store_true",
        help="Run non-interactively (assume 'yes' to prompts)"
    )
    parser.add_argument(
        "--logfile",
        type=Path,
        default=DEFAULT_LOGFILE,
        help="Path to the update log file"
    )
    return parser.parse_args()


def setup_logging(logfile: Path) -> None:
    """
    Configures logging to file and console with timestamps.
    """
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode="w"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    colorama.init(autoreset=True)
    logging.info(f"Log initialized at {logfile}")


def prompt_user(message: str, default: bool = False) -> bool:
    """
    Prompts the user for a yes/no answer.
    """
    if default:
        return True
    try:
        answer = input(f"{message} [y/N]: ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        logging.warning(Fore.RED + "User input cancelled.")
        return False


def main() -> None:
    args = parse_args()
    setup_logging(args.logfile)

    try:
        # Internet check
        if not check_internet():
            logging.error(Fore.RED + "No internet connection. Aborting.")
            sys.exit(1)
        logging.info(Fore.GREEN + "Internet connection detected.")

        # Define tasks
        tasks = [
            UpdateTask(
                name="macOS",
                check_cmd=["softwareupdate", "-l"],
                update_cmd=["softwareupdate", "-ia"],
                check_fn=lambda cp: "No new software available" not in cp.stdout
            ),
            UpdateTask(
                name="App Store (mas)",
                check_cmd=["mas", "outdated"],
                update_cmd=["mas", "upgrade"],
                check_fn=lambda cp: bool(cp.stdout.strip())
            ),
            UpdateTask(
                name="Homebrew (brew update)",
                check_cmd=["brew", "update", "--auto-update"],
                update_cmd=["brew", "update"],
                check_fn=lambda cp: "Auto-updated Homebrew" not in cp.stdout
            ),
            UpdateTask(
                name="Homebrew packages",
                check_cmd=["brew", "outdated", "--verbose"],
                update_cmd=["brew", "upgrade", "--greedy"],
                check_fn=lambda cp: bool(cp.stdout.strip())
            )
        ]

        # Parallel checks
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            check_futures = {executor.submit(task.check): task for task in tasks}
            pending_tasks = []
            for future in as_completed(check_futures):
                task = check_futures[future]
                try:
                    if future.result():
                        pending_tasks.append(task)
                except KeyboardInterrupt:
                    logging.warning(Fore.RED + "Update check cancelled by user.")
                    sys.exit(1)

        if not pending_tasks:
            logging.info(Fore.GREEN + "All systems are up to date. Exiting.")
            return

        # Confirm updates
        if not args.no_interaction and not prompt_user("Proceed with updates?"):
            logging.warning(Fore.RED + "Updates aborted by user.")
            return

        # Parallel updates
        with ThreadPoolExecutor(max_workers=len(pending_tasks)) as executor:
            update_futures = {executor.submit(task.update): task for task in pending_tasks}
            for future in as_completed(update_futures):
                task = update_futures[future]
                try:
                    success = future.result()
                    if not success:
                        logging.error(Fore.RED + f"{task.name} update encountered errors.")
                except KeyboardInterrupt:
                    logging.warning(Fore.RED + "Update process cancelled by user.")
                    sys.exit(1)

        logging.info(Fore.CYAN + f"Update process completed. See log at {args.logfile}")

    except KeyboardInterrupt:
        logging.warning(Fore.RED + "Operation cancelled by user (Ctrl+C). Exiting gracefully.")
        sys.exit(1)


if __name__ == "__main__":
    main()
