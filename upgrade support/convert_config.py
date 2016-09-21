import os
import json


def load(config_file):
    config = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if line.find('=') > 0:
                    t = (line.rstrip("\r\n")).split('=')
                    local_cw = t[0].split('.')
                    set_value = t[1]
                    config.update({local_cw[1]: set_value})
            f.close()
        print("Config file loaded.")
        return config
    else:
        return None


def save(config_file, config):
    try:
        f = open(config_file, "w")
    except Exception:
        print("Error writing to config file!")
        raise
    else:
        for k, v in config.iteritems():
            f.write("self.setup.%s=%s\n" % (k, v))
        f.close()
        print("Config file saved.")

# please edit location of an old bridge file
old_file = "/root/config.old.py"
# please edit location of a new bridge file
new_file = "/root/config.new.py"

config_data = load(old_file)
print config_data
if config_data is not None:
    save(new_file, config_data)
