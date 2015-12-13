#MAX!EQ3 library
Simple library for accessing ELV/EQ-3 MAX! cube. And this is quick&dirty readme.

##Example
```python
import maxeq3

eq3 = maxeq3.eq3data("your_ip_address", 62910)
eq3.readData(False)
```

##Some variables
* to check returned error `self.return_error` list is used

##Issues
* no literal processing
* no auto update
* no interval scaling
* not heavily tested

Well, that was very short and quick :)