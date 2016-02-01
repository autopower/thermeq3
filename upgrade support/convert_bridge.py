import os
import json


def load(bridge_file):
    bridge = {}
    if os.path.exists(bridge_file):
        with open(bridge_file, "r") as f:
            for line in f:
                t = (line.rstrip("\r\n")).split('=')
                local_cw = t[0]
                set_value = t[1]
                bridge.update({local_cw: set_value})
            f.close()
        print("Bridge file loaded.")
        return bridge
    else:
        return None


def load_new(bridgefile):
    data = {}

    if os.path.exists(bridgefile):
        with open(bridgefile, "r") as f:
            try:
                data = json.load(f)
            except:
                raise
            finally:
                f.close()
        print("Bridge file loaded, new method.")
    else:
        print("Error loading bridge file!")
        data = None
    return data


def save(bridge_file, bridge):
    try:
        f = open(bridge_file, "w")
    except Exception:
        print("Error writing to bridge file!")
        raise
    else:
        f.write(json.dumps(bridge, sort_keys=True))
        f.close()
        print("Bridge file saved.")

# please edit location of an old bridge file
old_file = "/root/old.bridge"
# # please edit location of a new bridge file
new_file = "/root/new.bridge"

bridge_data = load(old_file)
if bridge_data is not None:
    save(new_file, bridge_data)

new_bridge = load_new(new_file)
print "Lists identical: ", bridge_data == new_bridge
