import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px 
from plotly.offline import init_notebook_mode
init_notebook_mode(connected=True)
import re
pd.set_option('display.max_columns' , None)
import warnings
warnings.filterwarnings('ignore')

dataset = pd.read_csv('/kaggle/input/imbd-dataset/IMBD.csv')
df = pd.DataFrame(dataset)
print('View of dataset:')
df.sample(7)