import sys
import os
import pandas as pd
sys.path.insert(0, os.path.abspath('a:/Master class/XAI - Concer recogination/tkinter_ui'))
from logic.model_manager import ModelManager

print('Testing Counterfactuals...')
mm = ModelManager('a:/Master class/XAI - Concer recogination/tkinter_ui')
inputs = {feat: 100.0 for feat in mm.feature_names}
print('Inputs:', inputs)
try:
    res = mm.get_counterfactual_recommendations('Random Forest', inputs, data_path='a:/Master class/XAI - Concer recogination/tkinter_ui/cancer_biomarkers.xlsx')
    print('Result:', res)
except Exception as e:
    print('Error:', e)
