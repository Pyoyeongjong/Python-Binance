import pprint
import pandas as pd
import numpy as np

dates = pd.date_range('20160101', periods=4)
data = [[1, 3, 5, 6],[1, 2, 3, 4]]
s = pd.DataFrame(data, columns=list('ABCD'))
ss = s.describe()
print(ss[ss['A'].isin([1])])
sss = s.T
print(sss[0])


