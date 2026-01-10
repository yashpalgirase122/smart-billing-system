import numpy as np
from sklearn.linear_model import LinearRegression

def train_and_predict(sales):
    X = np.arange(len(sales)).reshape(-1,1)
    y = np.array(sales)

    model = LinearRegression()
    model.fit(X, y)

    future = model.predict([[len(sales)]])
    return round(float(future[0]), 2)

def future_trend(sales):
    model = LinearRegression()
    X = np.arange(len(sales)).reshape(-1,1)
    model.fit(X, sales)

    return [round(float(model.predict([[i]])[0]),2) for i in range(len(sales)+6)]
