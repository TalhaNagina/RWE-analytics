"""
Real-World Evidence Analytics Engine
Performs multi-hospital analysis with privacy preservation
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import json


class RWEAnalyticsEngine:
    """
    Real-World Evidence Analytics for Ophthalmology
    
    Analyzes data from multiple hospitals without exposing raw patient data
    """
    
    def __init__(self, datasets: List[pd.DataFrame]):
        """
        Initialize with list of anonymized datasets
        
        Args:
            datasets: List of anonymized dataframes from multiple hospitals
        """
        self.datasets = datasets
        self.combined_data = pd.concat(datasets, ignore_index=True)
        self.n_hospitals = len(datasets)
        self.n_patients = len(self.combined_data)
        
        print(f"\n{'='*80}")
        print(f"📊 RWE ANALYTICS ENGINE INITIALIZED")
        print(f"{'='*80}")
        print(f"Hospitals: {self.n_hospitals}")
        print(f"Total Patients: {self.n_patients}")
        print(f"{'='*80}\n")
    
    def calculate_bcva_improvement(self) -> pd.DataFrame:
        """
        Calculate visual acuity improvement (Primary efficacy endpoint)
        
        Converts Snellen notation to logMAR for statistical analysis
        """
        
        print("📈 Analyzing BCVA Improvement...")
        
        def va_to_logmar(numerator, denominator):
            """Convert Snellen (6/18) to logMAR scale"""
            if denominator == 0 or pd.isna(denominator):
                return None
            return np.log10(denominator / numerator)
        
        # Calculate logMAR scores
        self.combined_data['logmar_baseline'] = self.combined_data.apply(
            lambda row: va_to_logmar(row['bcva_baseline_numerator'], row['bcva_baseline_denominator']),
            axis=1
        )
        
        self.combined_data['logmar_6m'] = self.combined_data.apply(
            lambda row: va_to_logmar(row['bcva_6m_numerator'], row['bcva_6m_denominator']),
            axis=1
        )
        
        # Calculate change in lines (1 line = 0.1 logMAR)
        self.combined_data['bcva_change_lines'] = (
            (self.combined_data['logmar_baseline'] - self.combined_data['logmar_6m']) / 0.1
        )
        
        # Group by molecule
        results = self.combined_data.groupby('molecule').agg({
            'bcva_change_lines': ['mean', 'std', 'count', 'median']
        }).round(2)
        
        results.columns = ['Mean_Lines', 'Std_Dev', 'N_Patients', 'Median_Lines']
        
        print("\n✅ BCVA Improvement Results:")
        print(results)
        print()
        
        return results
    
    def analyze_adverse_events(self) -> Dict:
        """
        Safety analysis - adverse events monitoring
        Critical for post-market surveillance
        """
        
        print("🛡️ Analyzing Safety Profile...")
        
        total_patients = len(self.combined_data)
        adverse_events = self.combined_data[self.combined_data['adverse_events'] == 1]
        
        # Event breakdown by type (if column exists after anonymization)
        event_breakdown = {}
        if 'event_type' in adverse_events.columns:
            event_breakdown = adverse_events['event_type'].value_counts().to_dict()
        else:
            # If event_type was removed, just show count
            event_breakdown = {'Various adverse events': len(adverse_events)}
        
        # Severity distribution (if column exists)
        severity_dist = {}
        if 'event_severity' in adverse_events.columns:
            severity_dist = adverse_events['event_severity'].value_counts().to_dict()
        else:
            severity_dist = {'Not categorized': len(adverse_events)}
        
        # By molecule
        ae_by_molecule = self.combined_data.groupby('molecule')['adverse_events'].agg([
            ('total_patients', 'count'),
            ('events', 'sum'),
            ('rate_percent', lambda x: (x.sum() / len(x)) * 100)
        ]).round(2)
        
        results = {
            'total_patients': total_patients,
            'total_adverse_events': len(adverse_events),
            'adverse_event_rate_percent': round((len(adverse_events) / total_patients) * 100, 2),
            'event_breakdown': event_breakdown,
            'severity_distribution': severity_dist,
            'by_molecule': ae_by_molecule.to_dict('index')
        }
        
        print("\n✅ Safety Profile:")
        print(f"  Total Patients: {total_patients}")
        print(f"  Adverse Events: {len(adverse_events)}")
        print(f"  Event Rate: {results['adverse_event_rate_percent']}%")
        if event_breakdown:
            print(f"\n  Event Types:")
            for event, count in list(event_breakdown.items())[:5]:  # Show top 5
                print(f"    - {event}: {count}")
        print()
        
        return results
    
    def injection_frequency_analysis(self) -> pd.DataFrame:
        """
        Analyze treatment burden and compliance
        
        Key RWE insight: Are patients getting enough injections?
        """
        
        print("💉 Analyzing Injection Frequency...")
        
        results = self.combined_data.groupby('molecule').agg({
            'injections_per_year': ['mean', 'median', 'std', 'min', 'max']
        }).round(2)
        
        results.columns = ['Mean', 'Median', 'Std_Dev', 'Min', 'Max']
        
        # Add clinical trial comparison (typical protocols)
        trial_protocols = {
            'Ranibizumab': 7,
            'Bevacizumab': 7,
            'Aflibercept': 6
        }
        
        results['Trial_Protocol'] = results.index.map(trial_protocols)
        results['Gap'] = results['Mean'] - results['Trial_Protocol']
        
        print("\n✅ Injection Frequency Results:")
        print(results)
        print(f"\n⚠️ GAP ANALYSIS: Real-world patients receive {abs(results['Gap'].mean()):.1f} fewer injections than trial protocols")
        print()
        
        return results
    
    def fluid_resolution_analysis(self) -> Dict:
        """
        Anatomical outcomes - OCT parameter analysis
        """
        
        print("🔬 Analyzing Anatomical Outcomes (OCT Parameters)...")
        
        # IRF resolution
        irf_baseline_positive = (self.combined_data['irf_baseline'] == 1).sum()
        irf_resolved = (
            (self.combined_data['irf_baseline'] == 1) & 
            (self.combined_data['irf_6m'] == 0)
        ).sum()
        
        # SRF resolution
        srf_baseline_positive = (self.combined_data['srf_baseline'] == 1).sum()
        srf_resolved = (
            (self.combined_data['srf_baseline'] == 1) & 
            (self.combined_data['srf_6m'] == 0)
        ).sum()
        
        # Hard exudates
        he_baseline_positive = (self.combined_data['hard_exudates_baseline'] == 1).sum()
        he_resolved = (
            (self.combined_data['hard_exudates_baseline'] == 1) & 
            (self.combined_data['hard_exudates_6m'] == 0)
        ).sum()
        
        results = {
            'irf_resolution_rate': round((irf_resolved / irf_baseline_positive) * 100, 1) if irf_baseline_positive > 0 else 0,
            'srf_resolution_rate': round((srf_resolved / srf_baseline_positive) * 100, 1) if srf_baseline_positive > 0 else 0,
            'hard_exudates_resolution_rate': round((he_resolved / he_baseline_positive) * 100, 1) if he_baseline_positive > 0 else 0,
            'details': {
                'irf': {'baseline': irf_baseline_positive, 'resolved': irf_resolved},
                'srf': {'baseline': srf_baseline_positive, 'resolved': srf_resolved},
                'hard_exudates': {'baseline': he_baseline_positive, 'resolved': he_resolved}
            }
        }
        
        print("\n✅ Anatomical Outcomes:")
        print(f"  IRF Resolution: {results['irf_resolution_rate']}%")
        print(f"  SRF Resolution: {results['srf_resolution_rate']}%")
        print(f"  Hard Exudates Resolution: {results['hard_exudates_resolution_rate']}%")
        print()
        
        return results
    
    def comorbidity_impact_analysis(self) -> pd.DataFrame:
        """
        Analyze how comorbidities affect treatment outcomes
        Real-world insight: Do diabetic patients respond differently?
        """
        
        print("🔍 Analyzing Comorbidity Impact...")
        
        results = self.combined_data.groupby('comorbidities').agg({
            'bcva_change_lines': ['mean', 'count'],
            'adverse_events': 'sum',
            'injections_per_year': 'mean'
        }).round(2)
        
        results.columns = ['BCVA_Improvement', 'N_Patients', 'Adverse_Events', 'Avg_Injections']
        
        print("\n✅ Comorbidity Impact:")
        print(results)
        print()
        
        return results
    
    def generate_rwe_report(self) -> Dict:
        """
        Generate comprehensive RWE report
        This is what Roche would use for regulatory submissions
        """
        
        print("\n" + "="*80)
        print("📋 GENERATING COMPREHENSIVE RWE REPORT")
        print("="*80 + "\n")
        
        report = {
            'metadata': {
                'n_hospitals': self.n_hospitals,
                'n_patients': self.n_patients,
                'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d')
            },
            'efficacy': {
                'bcva_improvement': self.calculate_bcva_improvement().to_dict('index')
            },
            'safety': self.analyze_adverse_events(),
            'treatment_burden': {
                'injection_frequency': self.injection_frequency_analysis().to_dict('index')
            },
            'anatomical_outcomes': self.fluid_resolution_analysis(),
            'subgroup_analysis': {
                'comorbidity_impact': self.comorbidity_impact_analysis().to_dict('index')
            }
        }
        
        print("\n" + "="*80)
        print("✅ RWE REPORT GENERATION COMPLETE")
        print("="*80 + "\n")
        
        return report
    
    def export_report(self, filepath: str = 'outputs/rwe_report.json'):
        """Export RWE report as JSON"""
        
        report = self.generate_rwe_report()
        
        # Convert to JSON-serializable format
        report_json = json.dumps(report, indent=2, default=str)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_json)
        
        print(f"✅ RWE report exported to: {filepath}")
        
        return report


def demo_analytics():
    """Demonstrate the analytics pipeline"""
    
    import os
    from privacy_engine import PrivacyEngine
    
    print("\n" + "="*80)
    print("RWE ANALYTICS DEMONSTRATION")
    print("="*80 + "\n")
    
    # Load and anonymize all datasets
    privacy_engine = PrivacyEngine(k_anonymity=5)
    
    anonymized_datasets = []
    hospitals = ['apollo_delhi', 'sankara_chennai', 'lvprasad_hyderabad']
    
    for hospital in hospitals:
        df = pd.read_csv(f'data/{hospital}_data.csv')
        df_anon = privacy_engine.anonymize(df, hospital.replace('_', ' ').title())
        anonymized_datasets.append(df_anon)
    
    # Initialize analytics engine
    analytics = RWEAnalyticsEngine(anonymized_datasets)
    
    # Generate comprehensive report
    report = analytics.export_report()
    
    print("\n" + "="*80)
    print("🎉 DEMO COMPLETE - Check outputs/ folder for reports")
    print("="*80 + "\n")


if __name__ == "__main__":
    demo_analytics()