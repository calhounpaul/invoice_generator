# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an invoice generator application that creates professional PDF invoices using ReportLab. The system uses a single Python script with JSON-based configuration for company info, invoice data, and PDF styling. All configuration is externalized to JSON files for easy customization without code changes.

## Key Commands

### First Time Setup
```bash
# Simply run the automated setup script - it handles everything!
./run.sh

# The script will automatically copy example files if they don't exist:
# - example.company_config.json → company_config.json
# - example.invoice_data.json → invoice_data.json
# Then edit the copied files with your actual company and client data
```

**Note**: The `run.sh` script automatically handles all dependencies and setup:
- Copies example configuration files if company_config.json and invoice_data.json don't exist
- Detects if conda is installed (checks PATH and `~/miniconda3`)
- If conda is not found, automatically downloads and installs Miniconda to `~/miniconda3`
- Creates the `invoice_generator` conda environment with Python 3.11
- Installs all required Python packages from `requirements.txt`
- Runs the invoice generator

### Setup and Installation

#### Automated Setup (Recommended)
```bash
# This single command handles everything:
# - Installs Miniconda if not present
# - Creates conda environment
# - Installs dependencies
# - Runs the invoice generator
./run.sh
```

#### Manual Setup with Conda
```bash
# If you already have conda installed or prefer manual control
conda create -n invoice_generator python=3.11 -y
conda run -n invoice_generator pip install -r requirements.txt
```

#### Manual Setup with venv (Alternative)
```bash
# If you prefer using Python's built-in venv instead of conda
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Generator
```bash
# Using the automated script (recommended)
./run.sh

# Direct execution with conda
conda run -n invoice_generator python invoice_generator.py

# Or with venv activated
python invoice_generator.py
```

### Miniconda Auto-Installation Details

The `run.sh` script includes automatic Miniconda installation (run.sh:7-44):

1. **Detection**: Checks if `conda` command exists in PATH or if `~/miniconda3` directory exists
2. **Download**: If not found, downloads latest Miniconda installer from https://repo.anaconda.com/miniconda/
3. **Silent Install**: Runs installer in batch mode (`-b` flag) with installation path `~/miniconda3`
4. **Initialization**: Automatically runs `conda init bash` to configure shell integration
5. **Cleanup**: Removes installer file after successful installation

After installation, the script:
- Verifies conda is accessible
- Creates `invoice_generator` environment with Python 3.11 if it doesn't exist
- Installs dependencies on first run (tracked by `.completed_installation` flag)
- Executes the invoice generator

**Manual Miniconda Installation** (if you prefer to install separately):
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda_installer.sh
bash miniconda_installer.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc
rm miniconda_installer.sh
```

## Architecture

### Core Components

**invoice_generator.py** - Single-file application containing:
- `create_invoice(company_data, invoice_data, output_dir)` - Main function that generates PDF invoices
- `load_pdf_config(config_path)` - Loads PDF configuration from JSON (invoice_generator.py:14-17)
- Font registration system using configurable font family (invoice_generator.py:23-27)
- ReportLab document generation with JSON-configured styles and layouts

**company_config.json** - Company information:
- Company name, address, email, logo path
- Tax ID (automatically masked in PDF output to show only last 4 digits)
- Payment terms and conditions

**invoice_data.json** - Invoice-specific data:
- Invoice number, dates, client information
- Services array supporting three item types:
  - **Hourly services**: `hours` + `rate` (e.g., consulting, development)
  - **Product items**: `quantity` + `unit_price` (e.g., hardware, software licenses)
  - **Fixed charges**: `amount` only (e.g., setup fees, flat-rate services)
- Payment status and dates
- Items are automatically categorized and displayed in separate sections with subtotals

**pdf_config.json** - PDF appearance configuration:
- Margins (all sides in points)
- Font paths and family name
- Paragraph styles (fontSize, leading, alignment for Normal, CompanyName, InvoiceTitle)
- Logo dimensions (maxWidth, maxHeight in inches)
- Table layout (availableWidth, columnWidths as percentages, cell padding, grid styling)
- Spacing configuration (afterCompanyInfo, afterInvoiceDetails, afterServicesTable, beforeTerms)

### PDF Generation Flow

1. **Configuration Loading** - PDF config loaded from pdf_config.json at module level (invoice_generator.py:20)
2. **Font Registration** - Fonts registered from paths in PDF config (invoice_generator.py:23-27)
3. **Document Creation** - SimpleDocTemplate with letter size and margins from pdf_config.json (invoice_generator.py:40-47)
4. **Style Configuration** - Custom paragraph styles (CompanyName, InvoiceTitle, RightAlign) created from pdf_config.json (invoice_generator.py:53-87)
5. **Content Building** - Story list populated in order:
   - Company logo (scaled maintaining aspect ratio, constraints from pdf_config.json)
   - Company information (with masked EIN showing only last 4 digits)
   - Invoice title
   - Invoice details table (invoice number, dates, client info)
   - **Categorized item sections** (invoice_generator.py:140-378):
     - PROFESSIONAL SERVICES section (if hourly items exist): Date | Description | Hours | Rate | Amount
     - ITEMS & PRODUCTS section (if quantity items exist): Date | Description | Qty | Unit Price | Amount
     - OTHER CHARGES section (if fixed amount items exist): Date | Description | Amount
     - Each section displays a subtotal
   - Grand total (TOTAL DUE) with bold formatting
   - Payment status (if provided)
   - Terms and conditions
6. **Output** - PDFs saved to outputs/ directory with format: `Invoice_{invoice_number}_{timestamp}.pdf`

### Important Implementation Details

- **Configuration-Driven**: All styling, fonts, margins, and layout settings come from pdf_config.json
- **Smart Section Categorization**: Items automatically categorized into three sections (invoice_generator.py:140-378):
  - Professional Services (hours + rate)
  - Items & Products (quantity + unit_price)
  - Other Charges (amount only)
  - Each section has appropriate column headers and displays subtotal
  - Grand total combines all sections
- **Table Text Wrapping**: All table cells use Paragraph objects to enable proper text wrapping
- **EIN Masking**: Tax ID automatically masked showing format `**-****{last4}` (invoice_generator.py:113-115)
- **Logo Scaling**: Maintains aspect ratio while constraining to dimensions from pdf_config.json (invoice_generator.py:94-104)
- **Flexible Item Calculation**: Supports three calculation methods (invoice_generator.py:161-176):
  - hours × rate for services
  - quantity × unit_price for products
  - Direct amount for fixed charges
- **Dynamic Column Widths**: Table columns calculated from availableWidth × percentages in pdf_config.json
- **Adaptive Layout**: Other Charges section uses 3-column layout while Services/Products use 5-column layout

## File Structure

```
invoice_generator/
├── invoice_generator.py       # Main application file
├── company_config.json        # Company information (gitignored - auto-copied from example)
├── invoice_data.json          # Invoice data (gitignored - auto-copied from example)
├── example.company_config.json # Example company configuration template
├── example.invoice_data.json  # Example invoice data template
├── pdf_config.json            # PDF appearance configuration
├── requirements.txt           # Python dependencies (reportlab)
├── run.sh                     # Automated setup and run script
├── .gitignore                 # Git ignore rules
├── CLAUDE.md                  # Developer instructions for Claude Code
├── assets/                    # Logo and images
│   └── logo_title.png
├── fonts/                     # Custom fonts
│   ├── LibreBaskerville-Regular.ttf
│   ├── LibreBaskerville-Bold.ttf
│   └── LibreBaskerville-Italic.ttf
└── outputs/                   # Generated PDF invoices (gitignored)
```

### Gitignore Configuration

The `.gitignore` file excludes sensitive and generated files from version control:
- `company_config.json` and `invoice_data.json` - Contains your identifying information
- `outputs/` - Generated PDF files
- `.completed_installation` - Installation flag file
- `.claude/` - Claude Code configuration
- Standard Python/conda/IDE files

The example configuration files (`example.company_config.json` and `example.invoice_data.json`) are tracked in git and serve as templates. The `run.sh` script automatically copies them to create your working configuration files on first run.

## Modifying the Application

### To Change Company Information
Edit `company_config.json` (automatically copied from `example.company_config.json` on first run if it doesn't exist) - includes name, address, email, logo path, tax ID, and payment terms.

### To Generate a New Invoice
Edit `invoice_data.json` (automatically copied from `example.invoice_data.json` on first run if it doesn't exist) with client details, services, and dates. The script reads this file when executed.

**Item Types** - Mix and match any of these three types in the `services` array:

1. **Hourly Services** - For time-based billing:
   ```json
   {
     "date": "Jan 5-10, 2025",
     "description": "Web Development",
     "hours": 24,
     "rate": 125.00
   }
   ```
   Appears in: PROFESSIONAL SERVICES section

2. **Product Items** - For quantity-based billing:
   ```json
   {
     "date": "Jan 2025",
     "description": "Mechanical Keyboard - Cherry MX Brown",
     "quantity": 3,
     "unit_price": 89.99
   }
   ```
   Appears in: ITEMS & PRODUCTS section

3. **Fixed Charges** - For flat-rate fees:
   ```json
   {
     "date": "Jan 2025",
     "description": "Project setup and deployment",
     "amount": 500.00
   }
   ```
   Appears in: OTHER CHARGES section

Each section automatically displays with appropriate headers and subtotals. The invoice shows a grand total combining all sections.

### To Customize PDF Appearance
Edit `pdf_config.json` to adjust:
- **Margins**: All sides in points (currently 30pt)
- **Fonts**: Font family name and paths to .ttf files
- **Styles**: fontSize, leading, alignment for Normal, CompanyName, and InvoiceTitle
- **Logo**: maxWidth and maxHeight in inches
- **Table**: availableWidth, columnWidths (as percentages), padding, grid styling
- **Spacing**: Vertical spacing between sections

### To Change Fonts
1. Add .ttf font files to fonts/ directory
2. Update pdf_config.json fonts section with new paths and family name
3. No code changes required

### To Adjust Table Layout
Modify pdf_config.json table.columnWidths - percentages must sum to 1.0. Current layout: Date (15%), Description (45%), Hours (12%), Rate (14%), Amount (14%).

### To Change Output Directory
Pass `output_dir` parameter to `create_invoice()` function (default: 'outputs/').
