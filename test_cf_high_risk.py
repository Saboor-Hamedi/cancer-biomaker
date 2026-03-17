import sys
import os
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.abspath('a:/Master class/XAI - Concer recogination/tkinter_ui'))
from logic.model_manager import ModelManager

print('Testing Counterfactuals...')
mm = ModelManager('a:/Master class/XAI - Concer recogination/tkinter_ui')
df = pd.read_excel('a:/Master class/XAI - Concer recogination/tkinter_ui/cancer_biomarkers.xlsx', sheet_name='Training_Data')
X, y = mm.get_training_data('a:/Master class/XAI - Concer recogination/tkinter_ui/cancer_biomarkers.xlsx')

model = mm.load_model('Random Forest')
probs = model.predict_proba(X)[:, 1]
high_risk_idx = np.argmax(probs)
print(f"Max Probs: {probs[high_risk_idx]}")
high_risk_inputs = X.iloc[high_risk_idx].to_dict()

print('High Risk Inputs:', high_risk_inputs)
try:
    res = mm.get_counterfactual_recommendations('Random Forest', high_risk_inputs, data_path='a:/Master class/XAI - Concer recogination/tkinter_ui/cancer_biomarkers.xlsx')
    print('Result:', res)
except Exception as e:
    import traceback
    traceback.print_exc()

# Also check GNN load
try:
    print('Loading GNN...')
    gnn = mm.load_model('Graph Neural Network')
    if gnn:
        print('GNN loaded successfully.')
    else:
        print('GNN could not be loaded.')
except Exception as e:
    import traceback
    traceback.print_exc()
