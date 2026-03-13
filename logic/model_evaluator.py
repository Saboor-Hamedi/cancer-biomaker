#!/usr/bin/env python3
"""
Model Statistics and Evaluation System
Provides comprehensive analysis and scoring of all trained models with recommendations.
"""

import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import cross_val_score, cross_validate

warnings.filterwarnings('ignore')

class ModelEvaluator:
    """
    Comprehensive model evaluation system that analyzes all trained models
    and provides detailed statistics, scoring, and recommendations.
    """

    def __init__(self):
        self.scoring_metrics = {
            'accuracy': 'Overall correctness of predictions',
            'precision': 'Ability to avoid false positives',
            'recall': 'Ability to find all positive cases',
            'f1': 'Balanced measure of precision and recall',
            'roc_auc': 'Ability to distinguish classes',
            'specificity': 'Ability to avoid false positives (TNR)',
            'npv': 'Ability to correctly identify negatives',
            'mcc': 'Correlation between predictions and actuals'
        }

        self.weights = {
            'accuracy': 0.20,
            'precision': 0.15,
            'recall': 0.15,
            'f1': 0.15,
            'roc_auc': 0.20,
            'specificity': 0.10,
            'npv': 0.05
        }

    def evaluate_all_models(self, models_dict, X_train, X_test, y_train, y_test):
        """
        Comprehensive evaluation of all models with detailed statistics and scoring.

        Parameters:
        models_dict (dict): Dictionary of model names to trained model instances
        X_train, X_test: Training and test features
        y_train, y_test: Training and test labels

        Returns:
        dict: Complete evaluation results with scores and recommendations
        """
        results = {}

        for model_name, model in models_dict.items():
            print(f"Evaluating {model_name}...")

            # Get predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # Get probabilities if available
            y_prob_train = None
            y_prob_test = None
            if hasattr(model, 'predict_proba'):
                y_prob_train = model.predict_proba(X_train)[:, 1]
                y_prob_test = model.predict_proba(X_test)[:, 1]

            # Calculate comprehensive metrics
            metrics = self._calculate_metrics(y_test, y_pred_test, y_prob_test)

            # Cross-validation scores
            cv_scores = self._cross_validation_scores(model, X_train, y_train)

            # Model characteristics
            characteristics = self._analyze_model_characteristics(model, model_name)

            # Calculate composite score
            composite_score = self._calculate_composite_score(metrics)

            results[model_name] = {
                'metrics': metrics,
                'cv_scores': cv_scores,
                'characteristics': characteristics,
                'composite_score': composite_score,
                'predictions': {
                    'train': y_pred_train,
                    'test': y_pred_test,
                    'probabilities': y_prob_test
                }
            }

        # Generate comparative analysis and recommendations
        analysis = self._generate_comparative_analysis(results)

        return {
            'individual_results': results,
            'comparative_analysis': analysis,
            'recommendations': self._generate_recommendations(results),
            'ranking': self._rank_models(results)
        }

    def _calculate_metrics(self, y_true, y_pred, y_prob=None):
        """Calculate comprehensive set of evaluation metrics."""
        # Basic classification metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # Confusion matrix for additional metrics
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        # Additional metrics
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0

        # Matthews Correlation Coefficient
        mcc = (tp * tn - fp * fn) / np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) if (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn) > 0 else 0

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'specificity': specificity,
            'npv': npv,
            'mcc': mcc,
            'confusion_matrix': cm
        }

        # ROC-AUC if probabilities available
        if y_prob is not None:
            try:
                roc_auc = roc_auc_score(y_true, y_prob)
                metrics['roc_auc'] = roc_auc

                # Precision-Recall AUC
                precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_prob)
                pr_auc = average_precision_score(y_true, y_prob)
                metrics['pr_auc'] = pr_auc

            except Exception as e:
                metrics['roc_auc'] = None
                metrics['pr_auc'] = None

        return metrics

    def _cross_validation_scores(self, model, X, y, cv=5):
        """Perform cross-validation and return comprehensive scores."""
        try:
            # Multiple scoring metrics
            scoring = ['accuracy', 'precision', 'recall', 'f1']
            cv_results = cross_validate(model, X, y, cv=cv, scoring=scoring, return_train_score=False)

            return {
                'accuracy': {
                    'mean': cv_results['test_accuracy'].mean(),
                    'std': cv_results['test_accuracy'].std(),
                    'scores': cv_results['test_accuracy']
                },
                'precision': {
                    'mean': cv_results['test_precision'].mean(),
                    'std': cv_results['test_precision'].std(),
                    'scores': cv_results['test_precision']
                },
                'recall': {
                    'mean': cv_results['test_recall'].mean(),
                    'std': cv_results['test_recall'].std(),
                    'scores': cv_results['test_recall']
                },
                'f1': {
                    'mean': cv_results['test_f1'].mean(),
                    'std': cv_results['test_f1'].std(),
                    'scores': cv_results['test_f1']
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _analyze_model_characteristics(self, model, model_name):
        """Analyze model characteristics and complexity."""
        characteristics = {
            'model_type': type(model).__name__,
            'model_name': model_name
        }

        # Model complexity indicators
        if hasattr(model, 'n_estimators'):
            characteristics['n_estimators'] = model.n_estimators

        if hasattr(model, 'max_depth'):
            characteristics['max_depth'] = model.max_depth

        if hasattr(model, 'C'):
            characteristics['regularization_C'] = model.C

        if hasattr(model, 'kernel'):
            characteristics['kernel'] = model.kernel

        # Feature importance if available
        if hasattr(model, 'feature_importances_'):
            characteristics['has_feature_importance'] = True
            characteristics['feature_importance_sum'] = np.sum(model.feature_importances_)
        else:
            characteristics['has_feature_importance'] = False

        return characteristics

    def _calculate_composite_score(self, metrics):
        """Calculate a composite score combining multiple metrics."""
        score = 0
        valid_metrics = 0

        for metric, weight in self.weights.items():
            if metric in metrics and metrics[metric] is not None:
                # Normalize to 0-1 scale (assuming metrics are already 0-1)
                metric_score = metrics[metric]
                score += metric_score * weight
                valid_metrics += 1

        # Adjust for missing metrics
        if valid_metrics > 0:
            score = score * (len(self.weights) / valid_metrics)

        return score

    def _generate_comparative_analysis(self, results):
        """Generate comparative analysis across all models."""
        analysis = {
            'best_performers': {},
            'trade_offs': {},
            'consistency_analysis': {},
            'clinical_recommendations': {}
        }

        # Find best performers for each metric
        metrics_to_compare = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'specificity']

        for metric in metrics_to_compare:
            best_score = -1
            best_model = None

            for model_name, result in results.items():
                if metric in result['metrics'] and result['metrics'][metric] is not None:
                    score = result['metrics'][metric]
                    if score > best_score:
                        best_score = score
                        best_model = model_name

            if best_model:
                analysis['best_performers'][metric] = {
                    'model': best_model,
                    'score': best_score
                }

        # Analyze trade-offs
        analysis['trade_offs'] = self._analyze_trade_offs(results)

        # Consistency analysis
        analysis['consistency_analysis'] = self._analyze_consistency(results)

        return analysis

    def _analyze_trade_offs(self, results):
        """Analyze precision-recall trade-offs and other balances."""
        trade_offs = {}

        # Precision vs Recall trade-off
        precision_recall = []
        for model_name, result in results.items():
            metrics = result['metrics']
            if 'precision' in metrics and 'recall' in metrics:
                precision_recall.append({
                    'model': model_name,
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1': metrics.get('f1', 0)
                })

        trade_offs['precision_recall_balance'] = precision_recall

        # Accuracy vs Complexity (if available)
        accuracy_complexity = []
        for model_name, result in results.items():
            metrics = result['metrics']
            chars = result['characteristics']

            complexity_score = 0
            if 'n_estimators' in chars and chars['n_estimators'] is not None:
                complexity_score += chars['n_estimators'] / 1000  # Normalize
            if 'max_depth' in chars and chars['max_depth'] is not None:
                complexity_score += chars['max_depth'] / 50  # Normalize

            if complexity_score > 0 and 'accuracy' in metrics:
                accuracy_complexity.append({
                    'model': model_name,
                    'accuracy': metrics['accuracy'],
                    'complexity': complexity_score
                })

        trade_offs['accuracy_complexity'] = accuracy_complexity

        return trade_offs

    def _analyze_consistency(self, results):
        """Analyze consistency across cross-validation folds."""
        consistency = {}

        for model_name, result in results.items():
            cv_scores = result.get('cv_scores', {})

            if 'accuracy' in cv_scores and hasattr(cv_scores['accuracy'], 'std'):
                std_dev = cv_scores['accuracy']['std']
                mean_acc = cv_scores['accuracy']['mean']

                # Coefficient of variation
                cv = std_dev / mean_acc if mean_acc > 0 else float('inf')

                consistency[model_name] = {
                    'cv_std': std_dev,
                    'cv_coefficient': cv,
                    'consistency_rating': 'High' if cv < 0.05 else 'Medium' if cv < 0.10 else 'Low'
                }

        return consistency

    def _generate_recommendations(self, results):
        """Generate clinical and technical recommendations."""
        recommendations = {
            'primary_recommendation': '',
            'clinical_use_case': '',
            'technical_notes': [],
            'alternative_models': [],
            'cautions': []
        }

        # Find best overall model
        best_model = max(results.items(), key=lambda x: x[1]['composite_score'])

        recommendations['primary_recommendation'] = (
            f"**{best_model[0]}** is recommended as the primary model with a composite score of {best_model[1]['composite_score']:.3f}. "
            f"It demonstrates the best overall balance of accuracy, reliability, and clinical utility."
        )

        # Clinical use case recommendations
        metrics = best_model[1]['metrics']
        if metrics.get('recall', 0) > 0.85:
            recommendations['clinical_use_case'] = "Excellent for high-sensitivity screening where missing positive cases is critical."
        elif metrics.get('precision', 0) > 0.85:
            recommendations['clinical_use_case'] = "Ideal for confirmatory testing where false positives need to be minimized."
        else:
            recommendations['clinical_use_case'] = "Suitable for general diagnostic support with balanced performance."

        # Technical notes
        for model_name, result in results.items():
            cv_scores = result.get('cv_scores', {})
            if 'accuracy' in cv_scores and cv_scores['accuracy']['std'] > 0.1:
                recommendations['technical_notes'].append(
                    f"{model_name} shows high variability (CV std: {cv_scores['accuracy']['std']:.3f}) - consider more stable alternatives."
                )

        # Alternative models
        sorted_models = sorted(results.items(), key=lambda x: x[1]['composite_score'], reverse=True)
        if len(sorted_models) > 1:
            recommendations['alternative_models'] = [
                f"{model[0]} (Score: {model[1]['composite_score']:.3f})"
                for model in sorted_models[1:3]  # Top 2 alternatives
            ]

        # Cautions
        for model_name, result in results.items():
            metrics = result['metrics']
            if metrics.get('recall', 1) < 0.7:
                recommendations['cautions'].append(
                    f"{model_name} has low sensitivity ({metrics['recall']:.3f}) - may miss positive cases."
                )
            if metrics.get('precision', 1) < 0.7:
                recommendations['cautions'].append(
                    f"{model_name} has low precision ({metrics['precision']:.3f}) - may produce false positives."
                )

        return recommendations

    def _rank_models(self, results):
        """Rank models by composite score."""
        ranking = []
        sorted_models = sorted(results.items(), key=lambda x: x[1]['composite_score'], reverse=True)

        for rank, (model_name, result) in enumerate(sorted_models, 1):
            ranking.append({
                'rank': rank,
                'model': model_name,
                'composite_score': result['composite_score'],
                'accuracy': result['metrics'].get('accuracy', 0),
                'f1_score': result['metrics'].get('f1', 0),
                'roc_auc': result['metrics'].get('roc_auc', 0)
            })

        return ranking

    def generate_evaluation_report(self, evaluation_results, output_file=None):
        """Generate a comprehensive evaluation report."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE MODEL EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        recommendations = evaluation_results['recommendations']
        report.append(recommendations['primary_recommendation'])
        report.append("")
        report.append(f"Clinical Use Case: {recommendations['clinical_use_case']}")
        report.append("")

        # Model Ranking
        report.append("MODEL RANKING")
        report.append("-" * 40)
        ranking = evaluation_results['ranking']
        for model in ranking:
            report.append(f"{model['rank']}. {model['model']}")
            report.append(f"   Composite Score : {model['composite_score']:.4f}")
            report.append(f"   Accuracy        : {model.get('accuracy', 0):.3f}")
            report.append(f"   F1 Score        : {model.get('f1_score', 0):.3f}")
            report.append(f"   ROC-AUC         : {model.get('roc_auc', 0) or 0:.3f}")
            report.append("")

        # Detailed Metrics
        report.append("DETAILED METRICS")
        report.append("-" * 40)
        for model_name, result in evaluation_results['individual_results'].items():
            report.append(f"\n{model_name}:")
            metrics = result['metrics']
            for metric, value in metrics.items():
                if metric == 'confusion_matrix':
                    continue  # Skip nested array
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    report.append(f"  {metric:<30}: {value:.4f}")

        # Cross-validation Scores
        report.append("\nCROSS-VALIDATION SCORES")
        report.append("-" * 40)
        for model_name, result in evaluation_results['individual_results'].items():
            cv = result.get('cv_scores', {})
            if 'accuracy' in cv and isinstance(cv['accuracy'], dict):
                mean = cv['accuracy'].get('mean', 0)
                std  = cv['accuracy'].get('std', 0)
                report.append(f"  {model_name:<25}: {mean:.4f} ± {std:.4f}")

        # Recommendations
        report.append("\nRECOMMENDATIONS")
        report.append("-" * 40)
        if recommendations['alternative_models']:
            report.append("Alternative Models:")
            for alt in recommendations['alternative_models']:
                report.append(f"  • {alt}")

        if recommendations['technical_notes']:
            report.append("\nTechnical Notes:")
            for note in recommendations['technical_notes']:
                report.append(f"  • {note}")

        if recommendations['cautions']:
            report.append("\nClinical Cautions:")
            for caution in recommendations['cautions']:
                report.append(f"  ⚠️  {caution}")

        report.append("\n" + "=" * 80)

        final_report = "\n".join(report)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(final_report)
            print(f"Report saved to: {output_file}")

        return final_report

def create_model_comparison_dashboard(evaluation_results):
    """
    Create a dashboard-style summary of model comparison.
    Returns a formatted string suitable for display.
    """
    dashboard = []
    dashboard.append("🏆 MODEL PERFORMANCE DASHBOARD")
    dashboard.append("=" * 50)

    ranking = evaluation_results['ranking']
    recommendations = evaluation_results['recommendations']

    # Top 3 models
    dashboard.append("\n🥇 TOP PERFORMERS")
    dashboard.append("-" * 30)
    for i, model in enumerate(ranking[:3], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        dashboard.append(f"{medal} {model['model']}: {model['composite_score']:.3f} (Acc: {model['accuracy']:.3f})")

    # Key insights
    dashboard.append("\n💡 KEY INSIGHTS")
    dashboard.append("-" * 30)
    dashboard.append(f"🏥 Best for Clinical Use: {ranking[0]['model']}")
    dashboard.append(f"📊 Highest Accuracy: {max(ranking, key=lambda x: x['accuracy'])['model']} ({max(ranking, key=lambda x: x['accuracy'])['accuracy']:.3f})")
    dashboard.append(f"🎯 Best ROC-AUC: {max(ranking, key=lambda x: x.get('roc_auc', 0))['model']} ({max(ranking, key=lambda x: x.get('roc_auc', 0))['roc_auc']:.3f})")

    # Recommendations
    dashboard.append("\n🎯 RECOMMENDATIONS")
    dashboard.append("-" * 30)
    dashboard.append(recommendations['primary_recommendation'])
    dashboard.append(f"\n💼 Clinical Application: {recommendations['clinical_use_case']}")

    if recommendations['cautions']:
        dashboard.append("\n⚠️  IMPORTANT CAUTIONS")
        dashboard.append("-" * 30)
        for caution in recommendations['cautions'][:3]:  # Show top 3 cautions
            dashboard.append(f"• {caution}")

    return "\n".join(dashboard)

# Convenience functions for easy use
def evaluate_models_comprehensive(models_dict, X_train, X_test, y_train, y_test, save_report=None):
    """
    One-stop function to evaluate all models comprehensively.

    Parameters:
    models_dict: Dictionary of {'model_name': model_instance}
    X_train, X_test, y_train, y_test: Standard train/test splits
    save_report: Optional file path to save detailed report

    Returns:
    dict: Complete evaluation results
    """
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_all_models(models_dict, X_train, X_test, y_train, y_test)

    if save_report:
        evaluator.generate_evaluation_report(results, save_report)

    return results

def get_model_dashboard(results):
    """Get a formatted dashboard summary."""
    return create_model_comparison_dashboard(results)

if __name__ == "__main__":
    print("Model Statistics and Evaluation System")
    print("Use evaluate_models_comprehensive() to analyze your models!")
    print("Example: results = evaluate_models_comprehensive(models_dict, X_train, X_test, y_train, y_test)")
