#!/usr/bin/env python3
"""
Complete Demo Workflow
Runs all components of the Ophthalmology RWE platform
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_generator import generate_all_hospitals
from privacy_engine import PrivacyEngine
from analytics_engine import RWEAnalyticsEngine
import pandas as pd


def main():
    """Run complete demo workflow"""
    
    print("\n" + "="*80)
    print("🏥 OPHTHALMOLOGY RWE PLATFORM - COMPLETE DEMO")
    print("="*80)
    print("\nYellowSense Technologies - Roche Pharma Challenge 2026")
    print("Privacy-Preserving Multi-Hospital Analytics\n")
    print("="*80 + "\n")
    
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    
    # Step 1: Generate Data
    print("\n" + "▶"*40)
    print("STEP 1: GENERATING SYNTHETIC HOSPITAL DATA")
    print("▶"*40 + "\n")
    
    if not os.path.exists('data/apollo_delhi_data.csv'):
        generate_all_hospitals()
    else:
        print("✓ Data already exists, skipping generation")
        print("  (Delete data/ folder to regenerate)")
    
    # Step 2: Privacy Pipeline
    print("\n" + "▶"*40)
    print("STEP 2: PRIVACY-PRESERVING ANONYMIZATION")
    print("▶"*40 + "\n")
    
    privacy_engine = PrivacyEngine(k_anonymity=5)
    
    hospitals = [
        ('apollo_delhi', 'Apollo Delhi'),
        ('sankara_chennai', 'Sankara Nethralaya Chennai'),
        ('lvprasad_hyderabad', 'LV Prasad Hyderabad')
    ]
    
    anonymized_datasets = []
    
    for filename, display_name in hospitals:
        df = pd.read_csv(f'data/{filename}_data.csv')
        df_anon = privacy_engine.anonymize(df, display_name)
        anonymized_datasets.append(df_anon)
    
    # Show before/after comparison
    print("\n" + "="*80)
    print("📊 BEFORE vs AFTER ANONYMIZATION")
    print("="*80 + "\n")
    
    original = pd.read_csv('data/apollo_delhi_data.csv')
    anonymized = anonymized_datasets[0]
    
    print("BEFORE (Raw Patient Data - Cannot be shared):")
    print(original[['patient_name', 'patient_id', 'age', 'diagnosis', 'bcva_baseline_denominator']].head(3))
    
    print("\nAFTER (Anonymized - Safe for Research):")
    print(anonymized[['anonymized_id', 'age_group', 'diagnosis', 'bcva_baseline_denominator']].head(3))
    print()
    
    # Generate compliance report
    print("\n" + "="*80)
    print("📄 GENERATING DPDP COMPLIANCE REPORT")
    print("="*80 + "\n")
    
    compliance_report = privacy_engine.generate_compliance_report('outputs/compliance_report.txt')
    
    # Simulate re-identification attack
    privacy_engine.simulate_re_identification_attack(anonymized_datasets[0])
    
    # Step 3: RWE Analytics
    print("\n" + "▶"*40)
    print("STEP 3: REAL-WORLD EVIDENCE ANALYTICS")
    print("▶"*40 + "\n")
    
    analytics = RWEAnalyticsEngine(anonymized_datasets)
    
    # Generate comprehensive report
    rwe_report = analytics.export_report('outputs/rwe_report.json')
    
    # Step 4: Summary
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE - KEY FINDINGS")
    print("="*80 + "\n")
    
    print("📊 Dataset Summary:")
    print(f"  - Total Hospitals: {analytics.n_hospitals}")
    print(f"  - Total Patients: {analytics.n_patients}")
    print(f"  - Consent Rate: {(analytics.combined_data['consent_provided'].sum() / len(original) * 100):.1f}%")
    
    print("\n💊 Treatment Effectiveness:")
    bcva_results = analytics.calculate_bcva_improvement()
    for molecule in bcva_results.index:
        mean_improvement = bcva_results.loc[molecule, 'Mean_Lines']
        n_patients = bcva_results.loc[molecule, 'N_Patients']
        print(f"  - {molecule}: +{mean_improvement} lines (N={int(n_patients)})")
    
    print("\n🛡️ Safety Profile:")
    safety = rwe_report['safety']
    print(f"  - Adverse Event Rate: {safety['adverse_event_rate_percent']}%")
    print(f"  - Total Events: {safety['total_adverse_events']}")
    
    print("\n💉 Injection Frequency:")
    inj_freq = analytics.injection_frequency_analysis()
    avg_injections = inj_freq['Mean'].mean()
    avg_trial = inj_freq['Trial_Protocol'].mean()
    gap = avg_trial - avg_injections
    print(f"  - Real-World Average: {avg_injections:.1f} injections/year")
    print(f"  - Trial Protocol: {avg_trial:.1f} injections/year")
    print(f"  - Gap: {gap:.1f} injections ({(gap/avg_trial*100):.0f}% under-treatment)")
    
    print("\n📁 Generated Files:")
    print("  ✓ outputs/compliance_report.txt")
    print("  ✓ outputs/rwe_report.json")
    
    print("\n" + "="*80)
    print("🎉 SUCCESS - Platform Ready for Demo Video Recording")
    print("="*80)
    
    print("\n📹 Next Steps:")
    print("  1. Review outputs/ folder for reports")
    print("  2. Run: streamlit run src/streamlit_app.py (for web dashboard)")
    print("  3. Record demo video showing these outputs")
    print("  4. Deploy to Google Cloud Run")
    
    print("\n" + "="*80)
    print("YellowSense Technologies | https://yellowsense.in")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)