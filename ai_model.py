# ai_model.py
import numpy as np
from sklearn.linear_model import LinearRegression

def train_and_predict(sales):
    """
    sales = list of past sales totals
    """
    if len(sales) < 2:
        return sales[-1] if sales else 0

    X = np.array(range(len(sales))).reshape(-1, 1)
    y = np.array(sales)

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.array([[len(sales)]])
    prediction = model.predict(future_X)[0]

    return round(float(prediction), 2)
