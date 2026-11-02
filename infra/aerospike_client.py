import os

import aerospike


def create_client():
    config = {
        "hosts": [
            (
                os.environ["AEROSPIKE_HOST"],
                int(os.environ.get("AEROSPIKE_PORT", "4000")),
            )
        ],
        "user": os.environ["AEROSPIKE_USER"],
        "password": os.environ["AEROSPIKE_PASSWORD"],
    }

    return aerospike.client(config)


try:
    client = create_client()
    print("Connected successfully!")

except Exception as ex:
    print("Connection Error:", ex)