"""
Display Formatter - Handles formatting and displaying analysis results.
"""

import tkinter as tk
from datetime import datetime

import numpy as np


class DisplayFormatter:
    """Handles formatting and displaying analysis results in the UI."""

    def __init__(self, layout_manager):
        self.layout_manager = layout_manager

    def display_prediction_results(self, prediction_data):
        """Display prediction results in the analysis tab."""
        tab_analysis = self.layout_manager.get_components()['tab_analysis']

        tab_analysis.text.config(state=tk.NORMAL)
        tab_analysis.text.delete("1.0", tk.END)

        # Header
        header = self._format_prediction_header(prediction_data)
        tab_analysis.text.insert(tk.END, header)

        # Model details
        model_details = self._format_model_details(prediction_data)
        tab_analysis.text.insert(tk.END, model_details)

        # Prediction results
        results = self._format_prediction_results(prediction_data)
        tab_analysis.text.insert(tk.END, results)

        # Feature contributions
        if 'feature_contributions' in prediction_data:
            contributions = self._format_feature_contributions(prediction_data['feature_contributions'])
            tab_analysis.text.insert(tk.END, contributions)

        # Clinical interpretation
        interpretation = self._format_clinical_interpretation(prediction_data)
        tab_analysis.text.insert(tk.END, interpretation)

        tab_analysis.text.config(state=tk.DISABLED)

    def display_batch_results(self, results_df):
        """Display batch prediction results."""
        tab_analysis = self.layout_manager.get_components()['tab_analysis']

        tab_analysis.text.config(state=tk.NORMAL)
        tab_analysis.text.delete("1.0", tk.END)

        # Header
        header = self._format_batch_header(results_df)
        tab_analysis.text.insert(tk.END, header)

        # Summary statistics
        summary = self._format_batch_summary(results_df)
        tab_analysis.text.insert(tk.END, summary)

        # Risk stratification
        stratification = self._format_risk_stratification(results_df)
        tab_analysis.text.insert(tk.END, stratification)

        tab_analysis.text.config(state=tk.DISABLED)

    def display_model_comparison(self, comparison_data):
        """Display model comparison results."""
        tab_analysis = self.layout_manager.get_components()['tab_analysis']

        tab_analysis.text.config(state=tk.NORMAL)
        tab_analysis.text.delete("1.0", tk.END)

        # Header
        header = self._format_comparison_header(comparison_data)
        tab_analysis.text.insert(tk.END, header)

        # Performance metrics
        metrics = self._format_comparison_metrics(comparison_data)
        tab_analysis.text.insert(tk.END, metrics)

        # Recommendations
        recommendations = self._format_comparison_recommendations(comparison_data)
        tab_analysis.text.insert(tk.END, recommendations)

        tab_analysis.text.config(state=tk.DISABLED)

    def display_feature_importance(self, importance_data):
        """Display feature importance analysis."""
        tab_analysis = self.layout_manager.get_components()['tab_analysis']

        tab_analysis.text.config(state=tk.NORMAL)
        tab_analysis.text.delete("1.0", tk.END)

        # Header
        header = self._format_importance_header(importance_data)
        tab_analysis.text.insert(tk.END, header)

        # Importance rankings
        rankings = self._format_importance_rankings(importance_data)
        tab_analysis.text.insert(tk.END, rankings)

        # Clinical insights
        insights = self._format_importance_insights(importance_data)
        tab_analysis.text.insert(tk.END, insights)

        tab_analysis.text.config(state=tk.DISABLED)

    def _format_prediction_header(self, data):
        """Format prediction header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        model_name = data.get('model_name', 'Unknown')

        header = f"🩺 CANCER DETECTION ANALYSIS REPORT\n"
        header += f"Model: {model_name}\n"
        header += f"Analysis Date: {timestamp}\n"
        header += "=" * 80 + "\n\n"

        return header

    def _format_model_details(self, data):
        """Format model details section."""
        details = "📊 MODEL CONFIGURATION\n"
        details += f"Algorithm: {data.get('model_name', 'N/A')}\n"
        details += f"Training Dataset: {data.get('dataset_size', 'N/A')} samples\n"
        details += f"Features Used: {len(data.get('features', []))}\n"
        details += f"Prediction Confidence: {data.get('confidence', 0):.1f}%\n\n"

        return details

    def _format_prediction_results(self, data):
        """Format prediction results section."""
        prediction = data.get('prediction', 'UNKNOWN')
        probability = data.get('probability', 0.0)

        results = "🔍 PREDICTION RESULTS\n"

        if prediction.upper() == "POSITIVE":
            results += f"⚠️  DIAGNOSIS: POSITIVE for Cancer\n"
            results += f"   Probability: {probability:.1f}%\n"
            results += f"   Risk Level: HIGH\n"
        elif prediction.upper() == "NEGATIVE":
            results += f"✅ DIAGNOSIS: NEGATIVE for Cancer\n"
            results += f"   Probability: {probability:.1f}%\n"
            results += f"   Risk Level: LOW\n"
        else:
            results += f"❓ DIAGNOSIS: UNCERTAIN\n"
            results += f"   Probability: {probability:.1f}%\n"
            results += f"   Risk Level: UNKNOWN\n"

        results += "\n"

        # Add confidence interpretation
        if probability > 80:
            results += "💯 HIGH CONFIDENCE: Strong evidence supports this diagnosis.\n"
        elif probability > 60:
            results += "⚖️  MODERATE CONFIDENCE: Reasonable evidence supports this diagnosis.\n"
        else:
            results += "🤔 LOW CONFIDENCE: Limited evidence - consider additional testing.\n"

        results += "\n"

        return results

    def _format_feature_contributions(self, contributions):
        """Format feature contributions section."""
        section = "🔬 FEATURE CONTRIBUTIONS (Local Explanation)\n"
        section += "How each biomarker influenced this specific prediction:\n\n"

        # Sort by absolute contribution
        sorted_contribs = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

        for feature, contribution in sorted_contribs[:5]:  # Top 5
            direction = "↑" if contribution > 0 else "↓"
            impact = "increases" if contribution > 0 else "decreases"
            strength = "strongly" if abs(contribution) > 0.1 else "moderately" if abs(contribution) > 0.05 else "weakly"

            section += f"  {direction} {feature}: {strength} {impact} cancer risk\n"
            section += f"     Contribution: {contribution:+.3f}\n"

        section += "\n"
        return section

    def _format_clinical_interpretation(self, data):
        """Format clinical interpretation section."""
        prediction = data.get('prediction', 'UNKNOWN').upper()
        probability = data.get('probability', 0.0)

        interpretation = "🏥 CLINICAL INTERPRETATION\n"

        if prediction == "POSITIVE":
            interpretation += "⚠️  POSITIVE RESULT INTERPRETATION:\n"
            interpretation += "   • The model indicates elevated cancer risk based on biomarker profile\n"
            interpretation += "   • Probability suggests concerning biomarker patterns\n"
            interpretation += "   • RECOMMENDATION: Immediate clinical correlation required\n"
            interpretation += "   • NEXT STEPS: Additional diagnostic tests, specialist consultation\n"

            if probability > 85:
                interpretation += "   • URGENCY: High priority - expedited clinical review recommended\n"
            elif probability > 70:
                interpretation += "   • URGENCY: Moderate priority - clinical review within 1-2 weeks\n"
            else:
                interpretation += "   • URGENCY: Standard priority - routine clinical follow-up\n"

        elif prediction == "NEGATIVE":
            interpretation += "✅ NEGATIVE RESULT INTERPRETATION:\n"
            interpretation += "   • The model indicates low cancer risk based on biomarker profile\n"
            interpretation += "   • Biomarker patterns are within normal expected ranges\n"
            interpretation += "   • RECOMMENDATION: Continue routine screening as per guidelines\n"
            interpretation += "   • NEXT STEPS: Regular monitoring, standard preventive care\n"

        else:
            interpretation += "❓ UNCERTAIN RESULT INTERPRETATION:\n"
            interpretation += "   • The model cannot make a clear determination\n"
            interpretation += "   • Biomarker patterns show mixed or borderline signals\n"
            interpretation += "   • RECOMMENDATION: Additional testing or clinical evaluation needed\n"
            interpretation += "   • NEXT STEPS: Consider alternative diagnostic approaches\n"

        interpretation += "\n" + "⚠️  IMPORTANT MEDICAL DISCLAIMER:\n"
        interpretation += "   This is an AI-assisted screening tool, not a definitive diagnosis.\n"
        interpretation += "   All results must be interpreted by qualified medical professionals.\n"
        interpretation += "   Clinical decisions should never be based solely on AI predictions.\n"

        interpretation += "\n" + "=" * 80 + "\n"

        return interpretation

    def _format_batch_header(self, results_df):
        """Format batch results header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_samples = len(results_df)

        header = f"📋 BATCH PREDICTION SUMMARY REPORT\n"
        header += f"Total Samples Processed: {total_samples}\n"
        header += f"Analysis Date: {timestamp}\n"
        header += "=" * 80 + "\n\n"

        return header

    def _format_batch_summary(self, results_df):
        """Format batch summary statistics."""
        total = len(results_df)
        positive_count = len(results_df[results_df['Prediction'] == 'POSITIVE'])
        negative_count = total - positive_count

        positive_pct = (positive_count / total) * 100 if total > 0 else 0
        negative_pct = (negative_count / total) * 100 if total > 0 else 0

        summary = "📊 SUMMARY STATISTICS\n"
        summary += f"Total Predictions: {total}\n"
        summary += f"Positive Cases: {positive_count} ({positive_pct:.1f}%)\n"
        summary += f"Negative Cases: {negative_count} ({negative_pct:.1f}%)\n\n"

        # Probability distribution
        if 'Probability' in results_df.columns:
            avg_prob = results_df['Probability'].mean()
            max_prob = results_df['Probability'].max()
            min_prob = results_df['Probability'].min()

            summary += "🎯 PROBABILITY STATISTICS\n"
            summary += f"Average Probability: {avg_prob:.1f}%\n"
            summary += f"Highest Probability: {max_prob:.1f}%\n"
            summary += f"Lowest Probability: {min_prob:.1f}%\n\n"

        return summary

    def _format_risk_stratification(self, results_df):
        """Format risk stratification."""
        stratification = "🏥 RISK STRATIFICATION\n"

        if 'Probability' in results_df.columns:
            # Define risk categories
            high_risk = results_df[results_df['Probability'] > 75]
            medium_risk = results_df[(results_df['Probability'] > 50) & (results_df['Probability'] <= 75)]
            low_risk = results_df[results_df['Probability'] <= 50]

            stratification += f"High Risk (>75%): {len(high_risk)} cases\n"
            stratification += f"Medium Risk (50-75%): {len(medium_risk)} cases\n"
            stratification += f"Low Risk (≤50%): {len(low_risk)} cases\n\n"

            # Clinical recommendations
            stratification += "💡 CLINICAL RECOMMENDATIONS:\n"
            if len(high_risk) > 0:
                stratification += f"   • {len(high_risk)} cases require IMMEDIATE clinical attention\n"
            if len(medium_risk) > 0:
                stratification += f"   • {len(medium_risk)} cases need PRIORITY follow-up\n"
            if len(low_risk) > 0:
                stratification += f"   • {len(low_risk)} cases can follow STANDARD screening protocols\n"

        stratification += "\n" + "=" * 80 + "\n"
        return stratification

    def _format_comparison_header(self, data):
        """Format model comparison header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        header = f"⚖️  MODEL COMPARISON ANALYSIS\n"
        header += f"Analysis Date: {timestamp}\n"
        header += "=" * 80 + "\n\n"

        return header

    def _format_comparison_metrics(self, data):
        """Format comparison metrics."""
        metrics = "📈 PERFORMANCE METRICS COMPARISON\n\n"

        # Assuming data is a dict with model names as keys
        for model_name, model_data in data.items():
            metrics += f"{model_name}:\n"

            if 'accuracy' in model_data:
                metrics += f"  • Accuracy: {model_data['accuracy']:.3f}\n"
            if 'precision' in model_data:
                metrics += f"  • Precision: {model_data['precision']:.3f}\n"
            if 'recall' in model_data:
                metrics += f"  • Recall: {model_data['recall']:.3f}\n"
            if 'f1_score' in model_data:
                metrics += f"  • F1-Score: {model_data['f1_score']:.3f}\n"
            if 'auc' in model_data:
                metrics += f"  • AUC: {model_data['auc']:.3f}\n"

            metrics += "\n"

        return metrics

    def _format_comparison_recommendations(self, data):
        """Format comparison recommendations."""
        recommendations = "🎯 RECOMMENDATIONS\n\n"

        # Find best models for different criteria
        if data:
            # Best accuracy
            best_accuracy = max(data.items(), key=lambda x: x[1].get('accuracy', 0))
            recommendations += f"🏆 BEST OVERALL ACCURACY: {best_accuracy[0]}\n"

            # Best precision (for high-stakes positive predictions)
            best_precision = max(data.items(), key=lambda x: x[1].get('precision', 0))
            recommendations += f"🎯 BEST PRECISION: {best_precision[0]} (recommended for cancer screening)\n"

            # Best recall (for not missing cancer cases)
            best_recall = max(data.items(), key=lambda x: x[1].get('recall', 0))
            recommendations += f"🔍 BEST RECALL: {best_recall[0]} (recommended for comprehensive screening)\n"

            # Best AUC (balanced performance)
            best_auc = max(data.items(), key=lambda x: x[1].get('auc', 0))
            recommendations += f"⚖️  BEST BALANCED PERFORMANCE: {best_auc[0]}\n"

        recommendations += "\n💡 CLINICAL CONSIDERATIONS:\n"
        recommendations += "   • For cancer screening: Prioritize models with high recall to avoid missing cases\n"
        recommendations += "   • For resource allocation: Consider precision to minimize unnecessary procedures\n"
        recommendations += "   • For general use: Choose models with high AUC for balanced performance\n"

        recommendations += "\n" + "=" * 80 + "\n"
        return recommendations

    def _format_importance_header(self, data):
        """Format feature importance header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        model_name = data.get('model_name', 'Unknown')

        header = f"🔬 FEATURE IMPORTANCE ANALYSIS\n"
        header += f"Model: {model_name}\n"
        header += f"Analysis Date: {timestamp}\n"
        header += "=" * 80 + "\n\n"

        return header

    def _format_importance_rankings(self, data):
        """Format importance rankings."""
        rankings = "📊 FEATURE IMPORTANCE RANKINGS\n\n"

        features = data.get('features', [])
        importances = data.get('importances', [])

        if features and importances:
            # Sort by importance
            sorted_indices = np.argsort(importances)[::-1]

            for i, idx in enumerate(sorted_indices[:10]):  # Top 10
                feature = features[idx]
                importance = importances[idx]

                # Format importance as percentage
                importance_pct = importance * 100

                rankings += f"{i+1:2d}. {feature}\n"
                rankings += f"    Importance: {importance_pct:.2f}%\n"

                # Add clinical interpretation
                if importance_pct > 20:
                    rankings += "    → CRITICAL biomarker for cancer detection\n"
                elif importance_pct > 10:
                    rankings += "    → IMPORTANT contributor to diagnosis\n"
                elif importance_pct > 5:
                    rankings += "    → MODERATE influence on prediction\n"
                else:
                    rankings += "    → MINOR role in decision making\n"

                rankings += "\n"

        return rankings

    def _format_importance_insights(self, data):
        """Format importance insights."""
        insights = "💡 CLINICAL INSIGHTS\n\n"

        features = data.get('features', [])
        importances = data.get('importances', [])

        if features and importances:
            # Find most important features
            sorted_indices = np.argsort(importances)[::-1]
            top_features = [features[idx] for idx in sorted_indices[:3]]

            insights += "🔍 KEY FINDINGS:\n"
            insights += f"   • Primary biomarkers: {', '.join(top_features[:3])}\n"
            insights += "   • These features show the strongest correlation with cancer risk\n"
            insights += "   • Focus clinical validation efforts on these biomarkers\n\n"

            insights += "🏥 CLINICAL IMPLICATIONS:\n"
            insights += "   • Biomarker panels should prioritize highly important features\n"
            insights += "   • Less important features may be candidates for removal\n"
            insights += "   • Consider cost-benefit analysis for biomarker measurement\n\n"

            insights += "🔬 RESEARCH DIRECTIONS:\n"
            insights += "   • Investigate biological mechanisms of top biomarkers\n"
            insights += "   • Validate importance rankings with independent datasets\n"
            insights += "   • Explore feature interactions and combinations\n"

        insights += "\n" + "=" * 80 + "\n"
        return insights
