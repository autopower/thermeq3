#!/bin/ash
echo "Creating nsm.py compatibility file"
echo "#!/usr/bin/env python
import sys

sys.path.insert(0, \"/root/thermeq3/\")
execfile(\"/root/thermeq3/nsm.py\")
" > /root/nsm.py