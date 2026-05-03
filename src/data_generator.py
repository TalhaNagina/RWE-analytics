"""
Synthetic Ophthalmology Dataset Generator
Generates realistic patient data for RWE demonstration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class OphthalmologyDataGenerator:
    """Generate synthetic patient data for ophthalmology RWE"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.molecules = ['Ranibizumab', 'Bevacizumab', 'Aflibercept']
        self.diagnoses = ['AMD', 'DME', 'RVO']
        self.comorbidities = ['Diabetes', 'Hypertension', 'Both', 'None']
        
    def generate_hospital_data(self, hospital_name, n_patients, diagnosis_mix):
        """
        Generate realistic patient data for a hospital
        
        Args:
            hospital_name: Name of hospital (e.g., 'Apollo_Delhi')
            n_patients: Number of patients to generate
            diagnosis_mix: Dict of diagnosis distribution (e.g., {'AMD': 0.6, 'DME': 0.3})
        
        Returns:
            pandas DataFrame with patient records
        """
        print(f"Generating {n_patients} patients for {hospital_name}...")
        
        data = {
            # Hospital & Patient Info
            'hospital_id': [hospital_name] * n_patients,
            'patient_id': [f"{hospital_name[:3].upper()}{i:04d}" for i in range(n_patients)],
            'patient_name': [f"Patient_{hospital_name}_{i}" for i in range(n_patients)],
            'mrn': [f"MRN{np.random.randint(100000, 999999)}" for _ in range(n_patients)],
            
            # Demographics
            'age': np.random.normal(65, 12, n_patients).clip(40, 90).astype(int),
            'gender': np.random.choice(['M', 'F'], n_patients, p=[0.45, 0.55]),
            
            # Clinical Info
            'diagnosis': np.random.choice(
                list(diagnosis_mix.keys()), 
                n_patients, 
                p=list(diagnosis_mix.values())
            ),
            'comorbidities': np.random.choice(
                self.comorbidities, 
                n_patients, 
                p=[0.3, 0.25, 0.25, 0.2]
            ),
            'concomitant_medications': None,  # Will fill based on comorbidities
            
            # Treatment Details
            'molecule': np.random.choice(
                self.molecules, 
                n_patients,
                p=[0.4, 0.35, 0.25]
            ),
            'treatment_start_date': None,
            'injections_per_year': np.random.poisson(5.2, n_patients).clip(2, 12),
            
            # Efficacy Parameters - Baseline
            'bcva_baseline_numerator': [6] * n_patients,
            'bcva_baseline_denominator': np.random.choice(
                [12, 18, 24, 36, 60], 
                n_patients, 
                p=[0.1, 0.3, 0.3, 0.2, 0.1]
            ),
            
            # Efficacy Parameters - 6 Months
            'bcva_6m_numerator': [6] * n_patients,
            'bcva_6m_denominator': None,  # Will calculate
            
            # OCT Parameters
            'irf_baseline': np.random.choice([0, 1], n_patients, p=[0.3, 0.7]),
            'srf_baseline': np.random.choice([0, 1], n_patients, p=[0.4, 0.6]),
            'hard_exudates_baseline': np.random.choice([0, 1], n_patients, p=[0.6, 0.4]),
            'hrf_baseline': np.random.choice([0, 1], n_patients, p=[0.5, 0.5]),
            
            'irf_6m': None,
            'srf_6m': None,
            'hard_exudates_6m': None,
            'hrf_6m': None,
            
            # Safety
            'adverse_events': np.random.choice([0, 1], n_patients, p=[0.98, 0.02]),
            'event_type': None,
            'event_severity': None,
            
            # Compliance & Consent
            'consent_provided': np.random.choice([0, 1], n_patients, p=[0.05, 0.95]),
            'consent_date': None,
            'follow_up_compliance': np.random.choice(
                ['Excellent', 'Good', 'Fair', 'Poor'], 
                n_patients,
                p=[0.2, 0.4, 0.3, 0.1]
            )
        }
        
        df = pd.DataFrame(data)
        
        # Fill derived fields
        df = self._calculate_treatment_response(df)
        df = self._add_concomitant_medications(df)
        df = self._add_dates(df)
        df = self._add_adverse_events(df)
        
        print(f"✓ Generated {len(df)} records for {hospital_name}")
        return df
    
    def _calculate_treatment_response(self, df):
        """Simulate realistic treatment response based on injections and comorbidities"""
        
        for idx, row in df.iterrows():
            baseline_va = row['bcva_baseline_denominator']
            
            # Base improvement factor
            if row['injections_per_year'] >= 7:
                improvement_factor = np.random.uniform(0.5, 0.7)  # Good compliance
            elif row['injections_per_year'] >= 5:
                improvement_factor = np.random.uniform(0.4, 0.6)  # Moderate
            else:
                improvement_factor = np.random.uniform(0.2, 0.4)  # Poor compliance
            
            # Adjust for comorbidities (diabetics have worse outcomes)
            if row['comorbidities'] in ['Diabetes', 'Both']:
                improvement_factor *= 0.85
            
            # Calculate 6-month BCVA
            improved_denom = max(6, int(baseline_va * improvement_factor))
            df.at[idx, 'bcva_6m_denominator'] = improved_denom
            
            # OCT improvement (depends on injection frequency)
            resolution_prob = 0.5 + (row['injections_per_year'] - 5) * 0.05
            resolution_prob = np.clip(resolution_prob, 0.3, 0.8)
            
            df.at[idx, 'irf_6m'] = 1 if (row['irf_baseline'] == 1 and np.random.random() > resolution_prob) else 0
            df.at[idx, 'srf_6m'] = 1 if (row['srf_baseline'] == 1 and np.random.random() > resolution_prob) else 0
            df.at[idx, 'hard_exudates_6m'] = 1 if (row['hard_exudates_baseline'] == 1 and np.random.random() > resolution_prob * 0.7) else 0
            df.at[idx, 'hrf_6m'] = 1 if (row['hrf_baseline'] == 1 and np.random.random() > resolution_prob * 0.6) else 0
        
        return df
    
    def _add_concomitant_medications(self, df):
        """Add realistic medication lists based on comorbidities"""
        
        med_map = {
            'Diabetes': 'Metformin, Insulin',
            'Hypertension': 'Amlodipine, Atenolol',
            'Both': 'Metformin, Amlodipine, Aspirin',
            'None': 'None'
        }
        
        df['concomitant_medications'] = df['comorbidities'].map(med_map)
        return df
    
    def _add_dates(self, df):
        """Add realistic dates"""
        
        for idx in df.index:
            # Treatment start (6-18 months ago)
            start_date = datetime.now() - timedelta(days=np.random.randint(180, 540))
            df.at[idx, 'treatment_start_date'] = start_date.strftime('%Y-%m-%d')
            
            # Consent date (before treatment start)
            if df.at[idx, 'consent_provided'] == 1:
                consent_date = start_date - timedelta(days=np.random.randint(1, 30))
                df.at[idx, 'consent_date'] = consent_date.strftime('%Y-%m-%d')
        
        return df
    
    def _add_adverse_events(self, df):
        """Add adverse event details"""
        
        event_types = [
            'Transient IOP elevation',
            'Subconjunctival hemorrhage',
            'Eye pain',
            'Floaters',
            'Vitreous hemorrhage',
            'Endophthalmitis'
        ]
        
        event_severity = {
            'Transient IOP elevation': 'Mild',
            'Subconjunctival hemorrhage': 'Mild',
            'Eye pain': 'Mild',
            'Floaters': 'Mild',
            'Vitreous hemorrhage': 'Moderate',
            'Endophthalmitis': 'Severe'
        }
        
        for idx in df[df['adverse_events'] == 1].index:
            event = np.random.choice(event_types, p=[0.35, 0.3, 0.2, 0.1, 0.04, 0.01])
            df.at[idx, 'event_type'] = event
            df.at[idx, 'event_severity'] = event_severity[event]
        
        return df


def generate_all_hospitals():
    """Generate datasets for all 3 hospitals"""
    
    generator = OphthalmologyDataGenerator(seed=42)
    
    # Define hospital configurations
    hospitals = [
        {
            'name': 'Apollo_Delhi',
            'n_patients': 500,
            'diagnosis_mix': {'AMD': 0.6, 'DME': 0.3, 'RVO': 0.1}
        },
        {
            'name': 'Sankara_Chennai',
            'n_patients': 300,
            'diagnosis_mix': {'AMD': 0.4, 'DME': 0.5, 'RVO': 0.1}
        },
        {
            'name': 'LVPrasad_Hyderabad',
            'n_patients': 400,
            'diagnosis_mix': {'AMD': 0.5, 'DME': 0.35, 'RVO': 0.15}
        }
    ]
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    datasets = []
    for hospital in hospitals:
        df = generator.generate_hospital_data(
            hospital['name'],
            hospital['n_patients'],
            hospital['diagnosis_mix']
        )
        
        # Save to CSV
        filename = f"data/{hospital['name'].lower()}_data.csv"
        df.to_csv(filename, index=False)
        print(f"✓ Saved: {filename}")
        
        datasets.append(df)
    
    # Print summary
    print("\n" + "="*80)
    print("DATASET GENERATION COMPLETE")
    print("="*80)
    total_patients = sum(len(df) for df in datasets)
    print(f"Total Patients: {total_patients}")
    print(f"Consented: {sum(df['consent_provided'].sum() for df in datasets)}")
    print(f"Files saved in: ./data/")
    print("="*80)
    
    return datasets


if __name__ == "__main__":
    generate_all_hospitals()