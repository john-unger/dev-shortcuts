import subprocess
import re

# Function to run a shell command and get the output
def run_git_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()

# Function to get the current branch name
def get_current_branch():
    return run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])

# Function to get the common ancestor (merge base) between the current branch and develop
def get_merge_base(current_branch, base_branch="develop"):
    return run_git_command(["git", "merge-base", current_branch, base_branch])

# Function to get merge commits on the current branch since diverging from develop
def get_merged_branches(merge_base, current_branch):
    log_output = run_git_command(["git", "log", "--merges", "--pretty=format:%h %s", f"{merge_base}..{current_branch}"])
    return log_output.splitlines()

# Function to extract Jira ticket numbers and branch names from commit messages
def extract_ticket_numbers_and_branch_names(merged_branches):
    ticket_info = []
    ticket_pattern = re.compile(r"([A-Z]+-\d+)")  # Jira tickets like "ABC-1234"
    branch_name_pattern = re.compile(r"remote-tracking branch 'origin/(.+?)'")  # Extract the branch name

    for branch in merged_branches:
        ticket_match = ticket_pattern.search(branch)
        branch_name_match = branch_name_pattern.search(branch)
        if ticket_match and branch_name_match:
            ticket_info.append((ticket_match.group(1), branch_name_match.group(1)))

    return ticket_info

# Function to get the PR URL using GitHub CLI based on the branch name
def get_pr_url_for_branch(branch_name):
    pr_url = run_git_command(["gh", "pr", "list", "--head", branch_name, "--json", "url", "--jq", ".[] | .url"])
    if pr_url:
        return pr_url
    return f"(PR for {branch_name} not found)"

# Function to generate the Markdown table with Jira tickets and PR links
def generate_markdown_table(ticket_info):
    table_header = "| Jira Ticket | Pull Request |\n|-------------|--------------|"
    table_rows = []

    for ticket, branch_name in ticket_info:
        pr_url = get_pr_url_for_branch(branch_name)  # Use branch name to find the PR
        table_rows.append(f"| [{ticket}](https://perfectsense.atlassian.net/browse/{ticket}) | {pr_url} |")

    return f"{table_header}\n" + "\n".join(table_rows)

# Main function
def main():
    # Get the current branch
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")

    # Get the merge base between the current branch and develop
    merge_base = get_merge_base(current_branch)
    print(f"Merge base with 'develop': {merge_base}")

    # Get merged branches since the merge base
    merged_branches = get_merged_branches(merge_base, current_branch)

    # Extract Jira ticket numbers and branch names from merged branches
    ticket_info = extract_ticket_numbers_and_branch_names(merged_branches)

    if ticket_info:
        markdown_table = generate_markdown_table(ticket_info)
        print("Generated Markdown table:\n")
        print(markdown_table)
    else:
        print("No Jira tickets or PRs found in the merged commits.")

# Run the main function
if __name__ == "__main__":
    main()
