#!/usr/bin/env python3
"""
Quick test of SHAP plotting functionality
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Import our visualizer
from views.visualizations import Visualizer


def test_shap_plotting():
    """Test SHAP plotting with sample data"""
    print("Testing SHAP plotting...")

    # Create sample data
    np.random.seed(42)
    n_samples, n_features = 100, 10
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)

    # Train a simple model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Test SHAP plotting
    try:
        fig = Visualizer.plot_shap_analysis(model, X[:20], "Test Model")  # Use subset for faster testing
        print("✓ SHAP plotting successful")
        plt.close(fig)  # Clean up
        return True
    except Exception as e:
        print(f"✗ SHAP plotting failed: {e}")
        return False

if __name__ == "__main__":
    success = test_shap_plotting()
    sys.exit(0 if success else 1)
