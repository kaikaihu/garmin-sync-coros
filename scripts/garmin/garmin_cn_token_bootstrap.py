"""Create a reusable Garmin China garth session on a trusted local machine."""

from getpass import getpass

import garth


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def create_token(email, password, garth_client=garth):
    garth_client.configure(domain="garmin.cn")
    session = getattr(getattr(garth_client, "client", None), "sess", None)
    if session is not None:
        session.headers.update({"User-Agent": BROWSER_USER_AGENT})
    garth_client.login(email, password)
    serializer = getattr(garth_client, "dumps", None)
    if serializer is None:
        serializer = garth_client.client.dumps
    return serializer()


def main():
    email = input("Garmin China email: ").strip()
    password = getpass("Garmin China password: ")
    if not email or not password:
        print("Email and password are required.")
        return 2

    try:
        token = create_token(email, password)
    except Exception as err:
        if "429" not in str(err):
            raise
        print(
            "Garmin China login received HTTP 429. Stop retrying and wait "
            "before making one later attempt."
        )
        return 75

    print("\nAdd this value to the GitHub Actions secret GARMIN_CN_GARTH_TOKEN:")
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
