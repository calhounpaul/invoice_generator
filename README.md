# Invoice Generator

A professional PDF invoice generator built with Python and ReportLab. Generate beautiful, customizable invoices with automatic configuration management and a streamlined setup process.

## Features

- **Professional PDF Generation**: Create polished invoices with custom fonts and layouts
- **Smart Section Categorization**: Automatically splits services, products, and charges into separate sections with subtotals
- **JSON Configuration**: All settings externalized - no code changes needed
- **Automated Setup**: One command to install dependencies and generate invoices
- **Privacy-Focused**: Automatic EIN/Tax ID masking (shows only last 4 digits)
- **Flexible Pricing**: Support for hourly rates, quantity-based pricing, or fixed amounts
- **Custom Branding**: Add your logo and company information
- **Auto-Configuration**: Automatically copies example files on first run

## Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd invoice_generator

# Run the automated setup (handles everything!)
./run.sh
```

That's it! The script will:
1. Install Miniconda (if not already installed)
2. Create a Python 3.11 environment
3. Install all dependencies
4. Copy example configuration files
5. Generate your first invoice

After the first run, edit `company_config.json` and `invoice_data.json` with your actual information.

## Requirements

- Linux/macOS (or WSL on Windows)
- Bash shell
- Internet connection (for initial Miniconda installation)

No manual Python or conda installation required - `run.sh` handles it all!

## Installation

### Automated (Recommended)

```bash
./run.sh
```

The script automatically:
- Detects or installs Miniconda to `~/miniconda3`
- Creates the `invoice_generator` conda environment
- Installs all Python dependencies
- Copies example configuration files if they don't exist
- Runs the invoice generator

### Manual Setup

If you prefer manual control:

#### With Conda
```bash
conda create -n invoice_generator python=3.11 -y
conda run -n invoice_generator pip install -r requirements.txt
cp example.company_config.json company_config.json
cp example.invoice_data.json invoice_data.json
# Edit the JSON files with your information
conda run -n invoice_generator python invoice_generator.py
```

#### With venv
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp example.company_config.json company_config.json
cp example.invoice_data.json invoice_data.json
# Edit the JSON files with your information
python invoice_generator.py
```

## Configuration

### Company Information (`company_config.json`)

```json
{
  "company_name": "Your Company Name",
  "address": "123 Main St, City, ST 12345",
  "email": "billing@yourcompany.com",
  "logo_path": "assets/logo_title.png",
  "tax_id": "12-3456789",
  "payment_terms": "Payment is due within 30 days..."
}
```

**Note**: Tax ID is automatically masked in PDFs to show only the last 4 digits (e.g., `**-****6789`)

### Invoice Data (`invoice_data.json`)

```json
{
  "invoice_number": "INV-2025-001",
  "invoice_date": "2025-01-15",
  "due_date": "2025-02-14",
  "client_name": "Client Company",
  "client_address": "456 Oak Ave, Town, ST 67890",
  "services": [
    {
      "date": "2025-01-10",
      "description": "Web Development Services",
      "hours": 24,
      "rate": 125.00
    },
    {
      "date": "2025-01-12",
      "description": "Mechanical Keyboard - Cherry MX Brown",
      "quantity": 3,
      "unit_price": 89.99
    },
    {
      "date": "2025-01-15",
      "description": "Project setup and deployment",
      "amount": 500.00
    }
  ],
  "payment_status": "Paid on 2025-02-01"
}
```

**Automatic Section Categorization**: The invoice generator automatically organizes items into separate sections based on their type:

1. **PROFESSIONAL SERVICES** (hourly billing):
   - Use `hours` + `rate` fields
   - Displays as: Date | Description | Hours | Rate | Amount
   - Example: `"hours": 24, "rate": 125.00` → $3,000.00

2. **ITEMS & PRODUCTS** (quantity-based):
   - Use `quantity` + `unit_price` fields
   - Displays as: Date | Description | Qty | Unit Price | Amount
   - Example: `"quantity": 3, "unit_price": 89.99` → $269.97

3. **OTHER CHARGES** (fixed amounts):
   - Use `amount` field only
   - Displays as: Date | Description | Amount
   - Example: `"amount": 500.00` → $500.00

Each section shows a subtotal, and a **TOTAL DUE** appears at the bottom with all charges combined.

### PDF Styling (`pdf_config.json`)

Customize the appearance of your invoices:

```json
{
  "margins": {
    "top": 30,
    "bottom": 30,
    "left": 30,
    "right": 30
  },
  "fonts": {
    "family": "LibreBaskerville",
    "regular": "fonts/LibreBaskerville-Regular.ttf",
    "bold": "fonts/LibreBaskerville-Bold.ttf",
    "italic": "fonts/LibreBaskerville-Italic.ttf"
  },
  "styles": {
    "Normal": {"fontSize": 10, "leading": 12},
    "CompanyName": {"fontSize": 16, "leading": 20, "alignment": "LEFT"},
    "InvoiceTitle": {"fontSize": 24, "leading": 28, "alignment": "CENTER"}
  },
  "logo": {
    "maxWidth": 2.5,
    "maxHeight": 1.5
  },
  "table": {
    "availableWidth": 7.5,
    "columnWidths": [0.15, 0.45, 0.12, 0.14, 0.14],
    "padding": 6,
    "gridStyle": ["GRID", [0, 0], [-1, -1], 0.5, "#CCCCCC"]
  }
}
```

## Usage

### Generate an Invoice

```bash
# Using the automated script
./run.sh

# Or directly with conda
conda run -n invoice_generator python invoice_generator.py

# Or with activated venv
python invoice_generator.py
```

### Output

Invoices are saved to the `outputs/` directory with the format:
```
Invoice_{invoice_number}_{timestamp}.pdf
```

Example: `Invoice_INV-2025-001_20251102_225642.pdf`

## Customization

### Change Fonts

1. Add your `.ttf` font files to the `fonts/` directory
2. Update the `fonts` section in `pdf_config.json`
3. No code changes required!

### Adjust Table Layout

Modify `pdf_config.json` → `table.columnWidths`. The five values represent percentages (must sum to 1.0):
- Date (default: 15%)
- Description (default: 45%)
- Hours (default: 12%)
- Rate (default: 14%)
- Amount (default: 14%)

### Update Logo

1. Add your logo image to the `assets/` directory
2. Update `logo_path` in `company_config.json`
3. Adjust `logo.maxWidth` and `logo.maxHeight` in `pdf_config.json` if needed

## File Structure

```
invoice_generator/
├── invoice_generator.py          # Main application
├── company_config.json           # Your company info (gitignored)
├── invoice_data.json             # Invoice data (gitignored)
├── example.company_config.json   # Template for company info
├── example.invoice_data.json     # Template for invoice data
├── pdf_config.json               # PDF styling configuration
├── requirements.txt              # Python dependencies
├── run.sh                        # Automated setup script
├── .gitignore                    # Git ignore rules
├── assets/                       # Logo files
├── fonts/                        # Custom fonts
└── outputs/                      # Generated PDFs (gitignored)
```

## Privacy & Security

- Configuration files with your information (`company_config.json`, `invoice_data.json`) are gitignored by default
- Generated invoices in `outputs/` are not tracked in version control
- Tax IDs are automatically masked in PDFs
- Example files contain dummy data for reference

## Troubleshooting

### "conda not found" error
The `run.sh` script should automatically install Miniconda. If it fails:
```bash
# Manually install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda_installer.sh
bash miniconda_installer.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc
rm miniconda_installer.sh
```

### "FileNotFoundError: company_config.json"
Run the setup script instead of calling Python directly:
```bash
./run.sh
```

Or manually copy the example files:
```bash
cp example.company_config.json company_config.json
cp example.invoice_data.json invoice_data.json
```

### Font issues
Ensure the font files exist in the `fonts/` directory and paths in `pdf_config.json` are correct.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Credits

Built with [ReportLab](https://www.reportlab.com/) - the powerful PDF generation library for Python.
