import os
import json


def load_old(old_config_file, new_config_file):
    cf_1 = ["self.devname", "self.max_ip", "self.fromaddr", "self.toaddr", "self.mailserver", "self.mailport",
            "self.frompwd", "self.owm_api_key", "self.location", "self.extport"]
    cf_2 = ["self.device_name", "self.max_ip", "self.from_addr", "self.to_addr", "self.mail_server", "self.mail_port",
            "self.from_pwd", "self.owm_api_key", "self.yahoo_location", "self.ext_port"]
    ncf = {}
    result = 0xFF
    if os.path.exists(old_config_file):
        try:
            f = open(old_config_file, "r")
        except IOError:
            result = 1
        else:
            num = 0
            for line in f:
                is_comment = line.find('#')
                if is_comment == 0:
                    pass
                else:
                    if is_comment > 0:
                        line = line[:-is_comment]
                    w = line.split("=")
                    wr = w[0].rstrip()
                    if not w[0] == "\n":
                        if "toaddr" in wr:
                            wv = w[1].lstrip().rstrip()
                        else:
                            wv = w[1].lstrip().rstrip().replace('"', '')
                        if wr in cf_1:
                            num += 1
                            idx = cf_1.index(wr)
                            ncf.update({cf_2[idx].replace("self.", ""): str(wv)})
            if num < len(cf_1):
                # some commands are missing
                result = 2
            else:
                # everything is ok
                result = 3
            f.close()
            try:
                f = open(new_config_file, "w")
            except IOError:
                result = 4
            else:
                json.dump(ncf, f)
                f.close()
                result = 0
    return result


def load(config_file):
    f = None
    result = {}
    try:
        f = open(config_file, "r")
    except IOError:
        pass
    else:
        if f is not None:
            result = json.load(f)
    finally:
        if f is not None:
            f.close()
    return result
