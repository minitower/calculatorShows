from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
import numpy as np

from hw import HoltWinters

class CVScore:
    def __init__(self, data, n_split):
        self.data = data
        self.n_split=n_split

    def timeseriesCVscore(self, x):
        # вектор ошибок
        errors = []

        values = self.data.values
        alpha, beta, gamma = x

        # задаём число фолдов для кросс-валидации
        tscv = TimeSeriesSplit(n_splits=self.n_split) 

        for train, test in tscv.split(values):

            model = HoltWinters(series=values[train], slen = 24, alpha=alpha, beta=beta, gamma=gamma, n_preds=len(test))
            model.triple_exponential_smoothing()

            predictions = model.result[-len(test):]
            actual = values[test]
            error = mean_squared_error(predictions, actual)
            errors.append(error)

        # Возвращаем средний квадрат ошибки по вектору ошибок 
        return np.mean(np.array(errors))
