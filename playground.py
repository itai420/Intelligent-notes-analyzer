# collection of examples
# https://github.com/aubio/aubio/tree/master/python/demos
import pandas as pd
if __name__ == '__main__':
    df = pd.DataFrame([(.21, .32), (.01, .67), (.66, .03), (.21, .18)],columns=['dogs', 'cats'])
    df.round(0)
    print(round(1.5, 0))
