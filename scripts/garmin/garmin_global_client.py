import os


class GarminGlobalUploader:
    def __init__(self, client):
        self.client = client

    def upload_activity(self, activity_path):
        try:
            self.client.upload_activity(activity_path)
            return "SUCCESS"
        except Exception as err:
            message = str(err).lower()
            if "duplicate activity" in message or ("409" in message and "duplicate" in message):
                return "DUPLICATE_ACTIVITY"
            raise


def create_global_client(email, password, tokenstore, client_factory=None):
    if client_factory is None:
        from garminconnect import Garmin

        client_factory = Garmin

    os.makedirs(tokenstore, exist_ok=True)
    client = client_factory(email=email, password=password, is_cn=False)
    client.login(tokenstore)
    return client


def create_global_uploader(email, password, tokenstore, client_factory=None):
    client = create_global_client(
        email,
        password,
        tokenstore,
        client_factory=client_factory,
    )
    return GarminGlobalUploader(client)
