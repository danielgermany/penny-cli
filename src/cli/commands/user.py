"""User management CLI commands."""

import click
import getpass
from rich.console import Console
from rich.table import Table
from ..formatters import print_success, print_error, print_info


@click.group()
def user():
    """Manage users and authentication."""
    pass


@user.command("register")
@click.argument("username")
@click.option("--email", "-e", help="Email address")
@click.option("--display-name", "-d", help="Display name")
@click.option("--password", "-p", is_flag=True, help="Set a password for this user")
@click.pass_context
def register_user(ctx, username, email, display_name, password):
    """
    Register a new user.

    Examples:
        finance user register john
        finance user register jane --email jane@example.com -d "Jane Doe"
        finance user register admin --password
    """
    container = ctx.obj["container"]

    try:
        # Get password if flag is set
        user_password = None
        if password:
            user_password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")

            if user_password != confirm:
                print_error("Passwords do not match")
                return

            if len(user_password) < 4:
                print_error("Password must be at least 4 characters")
                return

        # Create user
        user = container.auth_service().create_user(
            username=username,
            password=user_password,
            email=email,
            display_name=display_name
        )

        print_success(f"User created: {user['username']}")
        if user.get("display_name"):
            print_info(f"Display name: {user['display_name']}")
        if user.get("email"):
            print_info(f"Email: {user['email']}")

        # Ask if they want to switch to this user
        if click.confirm("\nSwitch to this user now?", default=True):
            container.auth_service().set_current_user(user["id"])
            print_success(f"Switched to user: {user['username']}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to create user: {str(e)}")
        raise


@user.command("login")
@click.argument("username")
@click.option("--password", "-p", is_flag=True, help="Prompt for password")
@click.pass_context
def login_user(ctx, username, password):
    """
    Login as a user (switch user).

    Examples:
        finance user login john
        finance user login admin --password
    """
    container = ctx.obj["container"]

    try:
        # Get password if needed
        user_password = None
        if password:
            user_password = getpass.getpass("Password: ")

        # Attempt login
        user = container.auth_service().login(username, user_password)

        print_success(f"Logged in as: {user['username']}")
        if user.get("display_name"):
            print_info(f"Display name: {user['display_name']}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to login: {str(e)}")
        raise


@user.command("logout")
@click.pass_context
def logout_user(ctx):
    """
    Logout (clear current session).

    This will switch back to the default user (ID=1).
    """
    container = ctx.obj["container"]

    try:
        current = container.auth_service().get_current_user()
        if current:
            print_info(f"Logging out: {current['username']}")

        container.auth_service().logout()
        print_success("Logged out")
        print_info("Switched to default user")

    except Exception as e:
        print_error(f"Failed to logout: {str(e)}")
        raise


@user.command("current")
@click.pass_context
def current_user(ctx):
    """Show currently logged in user."""
    container = ctx.obj["container"]
    config = ctx.obj["config"]

    try:
        # Refresh user ID from session
        user_id = config._get_current_user_id()
        user = container.user_repo().get_by_id(user_id)

        if not user:
            print_error(f"User ID {user_id} not found")
            return

        print_info(f"Current user: {user['username']} (ID: {user['id']})")
        if user.get("display_name"):
            print_info(f"Display name: {user['display_name']}")
        if user.get("email"):
            print_info(f"Email: {user['email']}")
        if user.get("last_login"):
            print_info(f"Last login: {user['last_login']}")

        # Show if password is set
        has_password = user.get("require_password", False)
        print_info(f"Password protected: {'Yes' if has_password else 'No'}")

    except Exception as e:
        print_error(f"Failed to get current user: {str(e)}")
        raise


@user.command("list")
@click.option("--all", "-a", is_flag=True, help="Show all users including inactive")
@click.pass_context
def list_users(ctx, all):
    """List all users."""
    container = ctx.obj["container"]

    try:
        users = container.auth_service().list_users(include_inactive=all)

        if not users:
            print_info("No users found.")
            return

        console = Console()
        table = Table(title="Users")

        table.add_column("ID", style="dim")
        table.add_column("Username", style="cyan")
        table.add_column("Display Name")
        table.add_column("Email")
        table.add_column("Password", justify="center")
        table.add_column("Active", justify="center")
        table.add_column("Last Login")

        for u in users:
            table.add_row(
                str(u["id"]),
                u["username"],
                u.get("display_name") or "-",
                u.get("email") or "-",
                "Yes" if u.get("require_password") else "No",
                "Yes" if u.get("is_active") else "No",
                u.get("last_login") or "Never"
            )

        console.print(table)
        print_info(f"\nTotal users: {len(users)}")

    except Exception as e:
        print_error(f"Failed to list users: {str(e)}")
        raise


@user.command("delete")
@click.argument("username")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_user(ctx, username, yes):
    """
    Deactivate a user.

    Examples:
        finance user delete john
        finance user delete temp-user -y
    """
    container = ctx.obj["container"]

    try:
        user = container.user_repo().get_by_username(username)
        if not user:
            print_error(f"User '{username}' not found")
            return

        if not user["is_active"]:
            print_info(f"User '{username}' is already inactive")
            return

        # Show user info
        print_info(f"User: {user['username']} (ID: {user['id']})")
        if user.get("display_name"):
            print_info(f"Display name: {user['display_name']}")

        if not yes:
            if not click.confirm(f"\nDeactivate user '{username}'?"):
                print_info("Deletion cancelled")
                return

        # Delete user
        container.auth_service().delete_user(user["id"])

        print_success(f"Deactivated user: {username}")
        print_info("User data is preserved but user cannot login")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to delete user: {str(e)}")
        raise


@user.command("password")
@click.argument("username", required=False)
@click.option("--remove", is_flag=True, help="Remove password requirement")
@click.pass_context
def change_password(ctx, username, remove):
    """
    Change user password.

    If no username provided, changes password for current user.

    Examples:
        finance user password          # Change own password
        finance user password john     # Change john's password
        finance user password john --remove  # Remove password
    """
    container = ctx.obj["container"]
    config = ctx.obj["config"]

    try:
        # Get user
        if username:
            user = container.user_repo().get_by_username(username)
            if not user:
                print_error(f"User '{username}' not found")
                return
        else:
            user_id = config._get_current_user_id()
            user = container.user_repo().get_by_id(user_id)

        if remove:
            # Remove password
            container.auth_service().remove_password(user["id"])
            print_success(f"Removed password for: {user['username']}")
        else:
            # Set new password
            new_password = getpass.getpass("New password: ")
            confirm = getpass.getpass("Confirm password: ")

            if new_password != confirm:
                print_error("Passwords do not match")
                return

            if len(new_password) < 4:
                print_error("Password must be at least 4 characters")
                return

            container.auth_service().change_password(user["id"], new_password)
            print_success(f"Password updated for: {user['username']}")

    except Exception as e:
        print_error(f"Failed to change password: {str(e)}")
        raise
