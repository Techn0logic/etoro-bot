import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np

excel = pd.ExcelFile('temp/PET_PRI_SPT_S1_M.xls')
df = excel.parse(excel.sheet_names[1])
df = df.rename(columns=dict(zip(df.columns, ['Date','WTI','Brent'])))
df = df[18:]
df.index = df['Date']
#df = df[['WTI','Brent']]

# model = ARIMA(df, order=(2, 1, 0))
# results_AR = model.fit(disp=-1)
# plt.plot(ts_log_diff)
# plt.plot(results_AR.fittedvalues, color='red')
# plt.title('RSS: %.4f'% sum((results_AR.fittedvalues-ts_log_diff)**2))

#
#plt.plot(moving_avg, color='red')

mod = sm.tsa.statespace.SARIMAX(df['WTI'].astype(float), trend='n', order=(0,1,0), seasonal_order=(0,1,1,12))
results = mod.fit()
predict = results.predict(dinamic=True)
plt.plot(predict, color='red')
ts_log_moving_avg_diff = df['WTI'].ewm(12).mean()
plt.plot(ts_log_moving_avg_diff, color='green')
plt.plot(df['WTI'], color='blue')
plt.savefig("temp/wti_and_brent_all_data.png",dpi=200)