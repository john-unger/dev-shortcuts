import os
import subprocess
from datetime import datetime

def echo_color_log(color, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}]: {message}\n"

    with open(LOGFILE, "a") as log_file:
        log_file.write(log_message)

    if color:
        print(f"\033[{color}m{message}\033[0m")
    else:
        print(message)

def check_internet_connectivity():
    try:
        subprocess.check_call(["ping", "-c", "1", "8.8.8.8"])
        return True
    except subprocess.CalledProcessError:
        return False

def check_for_macos_updates():
    echo_color_log("1;34", "\nChecking for macOS updates...")
    result = subprocess.run(["softwareupdate", "-l"], capture_output=True, text=True)
    if "No new software available" in result.stdout:
        echo_color_log("1;32", "macOS is up to date.")
    else:
        echo_color_log("1;33", "macOS update is available.")
        return True
    return False

def check_for_app_store_updates():
    echo_color_log("1;34", "\nChecking for App Store updates...")
    result = subprocess.run(["mas", "outdated"], capture_output=True, text=True)
    if any(line.startswith("[0-9]") for line in result.stdout.splitlines()):
        echo_color_log("1;33", "App Store updates are available.")
        return True
    else:
        echo_color_log("1;32", "App Store apps are up to date.")
        return False

def check_for_homebrew_updates():
    echo_color_log("1;34", "\nChecking for Homebrew updates...")
    result = subprocess.run(["brew", "update", "--auto-update"], capture_output=True, text=True)
    echo_color_log("", result.stdout)
    if "Auto-updated Homebrew" in result.stdout:
        echo_color_log("1;33", "Homebrew is updated.")
    else:
        echo_color_log("1;33", "Homebrew updates are available.")
        return True
    return False

def check_for_outdated_casks_and_packages():
    echo_color_log("1;34", "\nChecking for outdated casks and packages...")
    result = subprocess.run(["brew", "outdated", "--verbose"], capture_output=True, text=True)
    if result.stdout:
        echo_color_log("1;33", "Outdated casks and packages found:")
        echo_color_log("", result.stdout)
        return True
    else:
        echo_color_log("1;32", "No outdated casks or packages found.")
        return False

def main():
    global LOGFILE
    LOGFILE = os.path.expanduser("~/updatemac_log.txt")

    macos_update_pending = False
    app_store_update_pending = False
    homebrew_update_pending = False
    casks_update_pending = False

    # Overwrite the log file if it exists
    with open(LOGFILE, "w") as log_file:
        log_file.write(f"Updating log on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check internet connectivity
    if not check_internet_connectivity():
        echo_color_log("1;31", "Error: No internet connection. Aborting updates.")
        return

    echo_color_log("1;34", "Internet connection detected.")

    # Check for macOS updates
    if check_for_macos_updates():
        macos_update_pending = True

    # Check for App Store updates
    if check_for_app_store_updates():
        app_store_update_pending = True

    # Check for Homebrew updates
    if check_for_homebrew_updates():
        homebrew_update_pending = True

    # Check for outdated casks and packages
    if check_for_outdated_casks_and_packages():
        casks_update_pending = True

    # Ask for confirmation before proceeding with updates
    if macos_update_pending or app_store_update_pending or homebrew_update_pending or casks_update_pending:
        response = input("\nDo you want to proceed with updates? (y/n): ").strip().lower()

        if response not in ["y", "yes"]:
            echo_color_log("1;31", "Updates aborted by user.")
            return
    else:
        echo_color_log("1;32", "No updates pending. Exiting.")
        return

    # Perform updates if updates are pending
    if macos_update_pending:
        # Perform macOS update
        echo_color_log("1;34", "Updating macOS...")
        result = subprocess.run(["softwareupdate", "-ia"], capture_output=True, text=True)
        if result.returncode == 0:
            echo_color_log("1;32", "macOS update complete.")
        else:
            echo_color_log("1;31", "macOS update failed.")

    if app_store_update_pending:
        # Perform App Store update
        echo_color_log("1;34", "Updating App Store apps...")
        result = subprocess.run(["mas", "upgrade"], capture_output=True, text=True)
        if result.returncode == 0:
            echo_color_log("1;32", "App Store update complete.")
        else:
            echo_color_log("1;31", "App Store update failed.")

    if homebrew_update_pending:
        # Perform Homebrew update
        echo_color_log("1;34", "Updating Homebrew...")
        result = subprocess.run(["brew", "update"], capture_output=True, text=True)
        if result.returncode == 0:
            echo_color_log("1;32", "Homebrew update complete.")
        else:
            echo_color_log("1;31", "Homebrew update failed.")

    if casks_update_pending:
        # Upgrade outdated casks if any
        echo_color_log("1;34", "Upgrading outdated casks and packages...")
        result = subprocess.run(["brew", "update-all"], capture_output=True, text=True)
        if result.returncode == 0:
            echo_color_log("1;32", "Cask and package upgrade complete.")
        else:
            echo_color_log("1;31", "Cask and package upgrade failed.")


    # Print the log file location and instructions
    echo_color_log("1;34", "\nTo view the log, run the following command:")
    echo_color_log("1;34", f"bat {LOGFILE}")

if __name__ == "__main__":
    main()
