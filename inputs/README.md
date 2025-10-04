# Inputs Directory

This directory contains input files for the Resource Allocation system.

## Directory Structure

- **test_fixtures/**: Test data files that are committed to version control for CI/CD testing
- **Production files**: Real data files (gitignored for privacy and size)

## Test Fixtures

Test fixtures in `test_fixtures/` are minimal, synthetic data files used for automated testing:

- `test_scorecard.pdf`: Minimal DSP scorecard for testing scorecard parsing functionality
- Other test data files as needed

## Production Files (Not Committed)

The following file patterns are gitignored:
- Daily Summary Log files
- Routes files
- Day of Operations plans
- Real scorecard PDFs
- Vehicle data files
- Associate data files

These files should be placed directly in the `inputs/` directory but will not be committed to version control.

## Usage

### For Development
Place your real data files in the `inputs/` directory for local testing and development.

### For Testing
Use the files in `test_fixtures/` which are designed for automated CI/CD testing.
