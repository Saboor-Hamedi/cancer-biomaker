import numpy as np
import pandas as pd
from sklearn.metrics import mutual_info_score

class DiagnosticEngine:
    """Core engine for real-time clinical data analysis and population drift detection."""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        # Clinical Baselines from the "Gold Standard" training set (500 patients)
        self.baseline_stats = {
            'PSA': {'mean': 18000.0, 'std': 15000.0}, # Estimated from clinical notes
            'AFP': {'mean': 45.0, 'std': 25.0},
            'CA125': {'mean': 35.0, 'std': 15.0}
        }

    def analyze_batch(self, df):
        """Perform comprehensive batch analysis."""
        if df is None or df.empty:
            return {}
            
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {}

        results = {
            'correlations': self._get_biomarker_correlations(numeric_df),
            'drift': self._detect_population_drift(numeric_df),
            'signal_strength': self._calculate_signal_strength(numeric_df),
            'confidence_zones': self._analyze_confidence_zones(df)
        }
        return results

    def _get_biomarker_correlations(self, df):
        """Identify strong co-occurrence patterns between biomarkers."""
        corr = df.corr()
        # Find top 3 interesting correlations
        pairs = []
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if abs(val) > 0.4:
                    pairs.append({
                        'pair': (cols[i], cols[j]),
                        'score': val,
                        'strength': 'High' if abs(val) > 0.7 else 'Moderate'
                    })
        return sorted(pairs, key=lambda x: abs(x['score']), reverse=True)[:3]

    def _detect_population_drift(self, df):
        """Compare current batch against clinical baseline to detect diagnostic shifts."""
        alerts = []
        for marker, baseline in self.baseline_stats.items():
            # Find matching column
            match = [c for c in df.columns if marker.lower() in str(c).lower()]
            if match:
                col = match[0]
                batch_mean = df[col].mean()
                z_score = (batch_mean - baseline['mean']) / baseline['std']
                
                if abs(z_score) > 1.5:
                    direction = "HIGHER" if z_score > 0 else "LOWER"
                    alerts.append({
                        'marker': marker,
                        'shift': f"{abs(z_score):.1f}σ {direction}",
                        'severity': 'CRITICAL' if abs(z_score) > 2.5 else 'WARNING'
                    })
        return alerts

    def _calculate_signal_strength(self, df):
        """Determine which biomarkers dominate the current diagnostic signal."""
        # Simple variance-based signal strength as proxy for importance in unsupervised batch
        variances = df.var()
        total_var = variances.sum()
        if total_var == 0: return []
        
        normalized = (variances / total_var).sort_values(reverse=True)
        return [{'marker': m, 'impact': v} for m, v in normalized.items()][:5]

    def _analyze_confidence_zones(self, df):
        """Categorize the batch into predictive certainty bands."""
        if 'Risk_Score' not in df.columns:
            return {'certain': 0, 'ambiguous': 0, 'total': len(df)}
            
        risks = df['Risk_Score']
        # Ambiguous is between 40% and 60% risk
        ambiguous = len(risks[(risks > 0.4) & (risks < 0.6)])
        certain = len(df) - ambiguous
        
        return {
            'certain': certain,
            'ambiguous': ambiguous,
            'total': len(df),
            'ratio': certain / len(df) if len(df) > 0 else 0
        }
