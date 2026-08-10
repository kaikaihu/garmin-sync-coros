"""Create one reusable Garmin Global garth session token on a trusted machine."""

from getpass import getpass

import garth


def create_token(email, password, garth_client=garth):
    garth_client.login(email, password)
    serializer = getattr(garth_client, "dumps", None)
    if serializer is None:
        serializer = garth_client.client.dumps
    return serializer()


def main():
    email = input("Garmin Global email: ").strip()
    password = getpass("Garmin Global password: ")
    if not email or not password:
        print("Email and password are required.")
        return 2

    token = create_token(email, password)
    print("\nAdd this value to the GitHub Actions secret GARMIN_GLOBAL_GARTH_TOKEN:")
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
