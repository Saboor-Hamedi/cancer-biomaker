import numpy as np
import pandas as pd
from sklearn.metrics import mutual_info_score

class DiagnosticEngine:
    """Core engine for real-time clinical data analysis and population drift detection."""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        # Initial Clinical Baselines (Will be updated dynamically upon data upload/training)
        self.baseline_stats = {
            'PSA': {'mean': 18000.0, 'std': 15000.0},
            'AFP': {'mean': 45.0, 'std': 25.0},
            'CA125': {'mean': 35.0, 'std': 15.0}
        }

    def recalculate_baselines(self, df):
        """Update clinical baselines based on the current population dataset statistics."""
        if df is None or df.empty:
            return
            
        for marker in self.baseline_stats.keys():
            # Find matching column (PSA, AFP, CA125)
            match = [c for c in df.columns if marker.lower() in str(c).lower()]
            if match:
                col = match[0]
                # Extract numeric values, ignoring errors and NaN
                values = pd.to_numeric(df[col], errors='coerce').dropna()
                if not values.empty:
                    self.baseline_stats[marker]['mean'] = float(values.mean())
                    self.baseline_stats[marker]['std'] = float(values.std())
                    # ROBUSTNESS: Ensure standard deviation is never zero to prevent infinity in Z-score calculation
                    if self.baseline_stats[marker]['std'] == 0:
                        self.baseline_stats[marker]['std'] = 1.0

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
            'confidence_zones': self._analyze_confidence_zones(df),
            'archetype': self._identify_cohort_archetype(df),
            'clarity': self._calculate_diagnostic_entropy(df)
        }
        return results

    def _calculate_diagnostic_entropy(self, df):
        """Measure the Shannon entropy of risks to assess batch clarity (Signal-to-Noise)."""
        if 'Risk_Score' not in df.columns: return 0.0
        
        risks = pd.to_numeric(df['Risk_Score'], errors='coerce').fillna(0)
        if len(risks) < 10: return 0.5 # Default for small cohorts
        
        # Quantize risks into 10 clinical buckets (0-10, 10-20...)
        counts, _ = np.histogram(risks, bins=10, range=(0, 1))
        probs = counts / len(risks)
        probs = probs[probs > 0] # Shannon entropy ignoring zero bins
        
        entropy = -np.sum(probs * np.log2(probs))
        # Max entropy for 10 bins is log2(10) ~= 3.32
        max_entropy = np.log2(10)
        
        # Clarity is the inverse of Normalized Entropy
        clarity = 1.0 - (entropy / max_entropy)
        return float(np.clip(clarity, 0, 1))

    def _identify_cohort_archetype(self, df):
        """Categorize the entire batch into a clinical fingerprint archetype."""
        if df is None or df.empty: return "Unknown"
        
        # 1. Gather Aggregates
        avg_risk = 0
        if 'Risk_Score' in df.columns:
            avg_risk = pd.to_numeric(df['Risk_Score'], errors='coerce').mean()
            
        z_scores = {}
        for marker, baseline in self.baseline_stats.items():
            match = [c for c in df.columns if marker.lower() in str(c).lower()]
            if match:
                batch_mean = df[match[0]].mean()
                std = baseline.get('std', 1.0)
                if std == 0: std = 1.0
                z_scores[marker] = (batch_mean - baseline['mean']) / std
        
        # 2. Archetype Mapping Logic
        psa_z = z_scores.get('PSA', 0)
        afp_z = z_scores.get('AFP', 0)
        ca125_z = z_scores.get('CA125', 0)
        
        total_drift = abs(psa_z) + abs(afp_z) + abs(ca125_z)
        
        if avg_risk > 0.65:
            if psa_z > 1.5 and (afp_z > 1.5 or ca125_z > 1.5):
                return "Malignant-Aggressive (Multi-Biomarker Convergence)"
            return "High-Risk Suspicious (Targeted Signal)"
        
        if total_drift > 4.0 and avg_risk < 0.4:
            return "Inflammatory / Metabolic Noise (High Drift / Low Risk)"
            
        if total_drift < 1.0 and avg_risk < 0.3:
            return "Stable Clinical Baseline"
            
        if (psa_z < -1.5 or afp_z < -1.5):
            return "Atrophic / Systemic Suppression"
            
        return "Variant Presentation (Atypical Mixture)"

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
                # ROBUSTNESS FIX: Guard against division by zero if std is not provided or zero
                std = baseline.get('std', 1.0)
                if std == 0: std = 1.0 
                z_score = (batch_mean - baseline['mean']) / std
                
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
        
        normalized = (variances / total_var).sort_values(ascending=False)
        return [{'marker': m, 'impact': v} for m, v in normalized.items()][:5]

    def _analyze_confidence_zones(self, df):
        """Categorize the batch into predictive certainty bands."""
        if 'Risk_Score' not in df.columns:
            return {'certain': 0, 'ambiguous': 0, 'total': len(df)}
            
        # Clinical Conversion: Ensure Risk_Score is numeric (coerce placeholder strings to 0)
        risks = pd.to_numeric(df['Risk_Score'], errors='coerce').fillna(0)
        
        # Ambiguous is between 40% and 60% risk (The clinical 'Grey Zone')
        ambiguous = len(risks[(risks > 0.4) & (risks < 0.6)])
        certain = len(df) - ambiguous
        
        return {
            'certain': certain,
            'ambiguous': ambiguous,
            'total': len(df),
            'ratio': certain / len(df) if len(df) > 0 else 0
        }

    def get_individual_forensic(self, inputs, risk_score):
        """Analyze a single patient's biomarker profile relative to the clinical cohort."""
        biomarker_deviations = []
        
        for marker, baseline in self.baseline_stats.items():
            # Find matching key in inputs
            match = [k for k in inputs.keys() if marker.lower() in str(k).lower()]
            if match:
                val = float(inputs[match[0]])
                # ROBUSTNESS FIX: Guard against division by zero
                std = baseline.get('std', 1.0)
                if std == 0: std = 1.0
                z_score = (val - baseline['mean']) / std
                biomarker_deviations.append({
                    'marker': marker,
                    'value': val,
                    'z_score': z_score,
                    'deviation': f"{abs(z_score):.1f}σ {'Above' if z_score > 0 else 'Below'}",
                    'severity': 'CRITICAL' if abs(z_score) > 3.0 else 'WARNING' if abs(z_score) > 1.5 else 'NORMAL'
                })
        
        # Clinical Triage Category
        if risk_score > 0.85:
            triage = "Level 1: Immediate Oncology Consultation Required"
            action = "Immediate biopsy and multiparametric MRI within 7 days."
        elif risk_score > 0.65:
            triage = "Level 2: Urgent Diagnostic Follow-up"
            action = "Confirmatory blood test and diagnostic imaging within 14 days."
        elif risk_score > 0.35:
            triage = "Level 3: Elevated Vigilance"
            action = "3-month scheduled re-test to track biomarker velocity."
        else:
            triage = "Level 4: Routine Wellness Observation"
            action = "Standard annual clinical surveillance recommended."
            
        # Clinical Forensic Reasoning Tags
        tags = self._generate_forensic_tags(biomarker_deviations, risk_score)
            
        return {
            'deviations': sorted(biomarker_deviations, key=lambda x: abs(x['z_score']), reverse=True),
            'triage_level': triage,
            'primary_action': action,
            'metabolic_stability': "Unstable" if any(d['severity'] == 'CRITICAL' for d in biomarker_deviations) else "Stable",
            'tags': tags
        }

    def _generate_forensic_tags(self, deviations, risk):
        """Analyze deviations vs risk to provide qualitative forensic labels."""
        tags = []
        if not deviations: return tags
        
        z_dict = {d['marker']: d['z_score'] for d in deviations}
        psa_z = z_dict.get('PSA', 0)
        afp_z = z_dict.get('AFP', 0)
        ca125_z = z_dict.get('CA125', 0)
        
        high_biomarkers = sum(1 for z in z_dict.values() if z > 1.5)
        all_normal = all(abs(z) < 1.2 for z in z_dict.values())
        
        # 1. Mismatch Analysis
        if risk > 0.8:
            if all_normal: tags.append("Atypical Presentation (Hidden Signal)")
            elif high_biomarkers >= 2: tags.append("Multi-Biomarker Convergence")
            else: tags.append("Classical Malignant Signal")
        
        # 2. Inflammatory Recognition
        if risk < 0.4 and psa_z > 2.0:
            tags.append("Non-Malignant Inflammatory Spike")
            
        # 3. Systemic Profiles
        if all_normal and risk < 0.2:
            tags.append("Clinical Homeostasis")
        elif psa_z < -1.5 and afp_z < -1.5:
            tags.append("Systemic Suppression Profile")
            
        return tags

