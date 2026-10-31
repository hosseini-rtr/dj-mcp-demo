import os
import aerospike

config = {
    "hosts": [
        (os.environ["AEROSPIKE_HOST"]),
        int(os.environ.get("AEROSPIKE_PORT", 3000)),
    ]
}

config["user"] = os.environ.get("AEROSPIKE_USER", 3000)
config["password"] = os.environ.get("AEROSPIKE_PASSWORD", 3000)

try:
    client = aerospike.client(config)
    client.connect()
    print("Connected successfully!")

except Exception as ex:
    print("Connection Error:", ex)