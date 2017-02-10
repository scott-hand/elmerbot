import json
import sys
import yaml
from elmerbot.client import ElmerClient


def main():
    if len(sys.argv) != 2 or sys.argv[1] == "dev":
        mode = "development"
    else:
        mode = "production"
    settings = yaml.load(open("settings.yaml"))
    client = ElmerClient(settings[mode])
    print("Starting bot...")
    client.run()
    print("Exiting...")


if __name__ == "__main__":
    main()
