#MAX!EQ3 library
Simple library for accessing ELV/EQ-3 MAX! cube. And this is quick&dirty readme.

##Example
```python
import maxeq3

stp = maxeq3.eq3("your_ip_address", 62910)
stp.readData(False)
```

##Some variables
* to check returned error `self.return_error` list is used
* to store messages for logger `self.log_messages` list is used

Well, that was very short and quick :)