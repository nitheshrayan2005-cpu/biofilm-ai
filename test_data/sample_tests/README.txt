BIOFILMAI SAMPLE TESTS
======================

Six ready-to-run tests for the New Analysis page. Each folder holds the files to upload
and FORM_VALUES.txt with every value to copy and paste into the form.

  1. Test_1_MRSA_knee_implant_REAL                    REAL DATASET
  2. Test_2_Pseudomonas_diabetic_foot_REAL            REAL DATASET
  3. Test_3_Ecoli_urinary_catheter_REAL               REAL DATASET
  4. Test_4_Sepidermidis_central_line_NO_GENOME_REAL  REAL DATASET (missing-data test)
  5. Test_5_mature_biofilm_knee_SIMULATED             SIMULATED
  6. Test_6_no_biofilm_control_SIMULATED              SIMULATED

REAL DATASET tests use real data from published sources:
  - Genomes: BV-BRC (Bacterial and Viral Bioinformatics Resource Center) bacterial genomes
  - Raman spectra: Bacteria-ID dataset (Ho et al., Nature Communications, 2019),
    held-out test spectra
  The microscopy images and patient details in these tests are SIMULATED, because no
  real microscopy for the same samples is available.

SIMULATED tests are fully computer-generated (images, spectra and sequences).

All patient details are invented. Do not enter real patient names.

The website is in demo mode: every result is a simulated probability that does not
depend on the uploaded files. These tests check that the full workflow works end to end.
Test 4 deliberately leaves out the genome to check that missing data is handled.
