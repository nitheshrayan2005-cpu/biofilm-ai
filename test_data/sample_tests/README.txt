BIOFILMAI SAMPLE TESTS
======================

Eight ready-to-run tests for the New Analysis page. Each folder holds the files to upload
and FORM_VALUES.txt with every value to copy and paste into the form, plus the result
the results page should show.

  1. Test_1_MRSA_knee_implant_REAL                    REAL DATASET
  2. Test_2_Pseudomonas_diabetic_foot_REAL            REAL DATASET
  3. Test_3_Ecoli_urinary_catheter_REAL               REAL DATASET
  4. Test_4_Sepidermidis_central_line_NO_GENOME_REAL  REAL DATASET (missing-data test)
  5. Test_5_mature_biofilm_knee_SIMULATED             SIMULATED
  6. Test_6_no_biofilm_control_SIMULATED              SIMULATED
  7. Test_7_Sepidermidis_RP62A_pathogenic_REAL        REAL DATASET (NCBI RefSeq NC_002976.3)
  8. Test_8_Sepidermidis_ATCC12228_commensal_REAL     REAL DATASET (NCBI RefSeq NC_004461.1)

REAL DATASET tests use real data from published sources:
  - Genomes: BV-BRC (Tests 1-3) and NCBI RefSeq (Tests 7-8) bacterial genomes
  - Raman spectra: Bacteria-ID dataset (Ho et al., Nature Communications, 2019),
    held-out test spectra
  The microscopy images and patient details in these tests are SIMULATED, because no
  real microscopy for the same samples is available.

SIMULATED tests are fully computer-generated (images, spectra and sequences).

All patient details are invented. Do not enter real patient names.

Every uploaded file is measured (microscopy clustering, Raman matrix band, resistance and
biofilm genes, clinical risk factors), so the score depends on the files and the same
files always give the same score. Test 4 deliberately leaves out the genome to check
that missing data is handled. Test 6 is the negative control and should score low.
