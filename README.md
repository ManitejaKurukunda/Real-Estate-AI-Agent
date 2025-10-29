# 🏢 Real Estate AI Agent

> **"Show me multifamily properties with occupancy below 85%"**  
> → *Instant SQL generation, execution, and business insights*

Chat with your real estate portfolio data using natural language. Built for fund managers, investors, and analysts who need fast answers without SQL expertise.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![GPT-4](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![SQL Server](https://img.shields.io/badge/Database-SQL%20Server-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎬 Demo

**[▶️ Watch 2-Minute Demo Video](https://drive.google.com/file/d/1uax_kqKNa6IbpfQ8JlWWM3MSqL6uUX04/view?usp=sharing)**

![Chat Interface Demo](assets/demo-screenshot.png)

### Example Queries:
```
💬 "List all hospitality properties"
💬 "Show me debt maturing in Q1 2025"
💬 "What's the average NOI by property type?"
💬 "Which funds have IRR above 15%?"
```

---

## ✨ Key Features

### 🧠 **Intelligent SQL Generation**
- GPT-4 converts natural language to optimized SQL queries
- Schema-aware with validation rules from JSON data models
- Handles complex joins, aggregations, and date ranges

### 💬 **Conversation Memory**
- Multi-turn context retention for follow-up questions
- Edit and rerun previous queries
- Spelling correction and error handling

### 📊 **Business Intelligence**
- Auto-generated insights from query results
- Executive summaries and key metrics
- PowerPoint content recommendations

### 📥 **Multi-Format Exports**
- **CSV** - Raw data downloads
- **Excel** - Formatted workbooks with formulas
- **PDF** - Professional reports with charts
- **Email** - Automated delivery with attachments

### 🎨 **Modern UI/UX**
- Responsive data tables with sticky headers
- Real-time notifications and status updates
- Editable conversation history
- Sample question suggestions

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Engine** | OpenAI GPT-4 | SQL generation + business insights |
| **Backend** | Python 3.8+ | API orchestration and data processing |
| **Database** | SQL Server | Real estate investment data warehouse |
| **Data Processing** | Pandas, NumPy | Data transformation and analysis |
| **Frontend** | HTML5, JavaScript, CSS3 | Chat interface and visualizations |
| **Export** | openpyxl, reportlab | Multi-format report generation |

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8+
# SQL Server instance
# OpenAI API key
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/real-estate-ai-chat
cd real-estate-ai-chat
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Create .env file
OPENAI_API_KEY=your_openai_api_key_here
SQL_SERVER=your_server_name
SQL_DATABASE=RealEstatePortfolio
SQL_USERNAME=your_username
SQL_PASSWORD=your_password
```

4. **Initialize database** (optional - sample data)
```bash
python setup/create_sample_database.py
```

5. **Run the application**
```bash
python server.py
# Open browser to http://localhost:8000
```

---

## 🏗️ Architecture

### **Data Warehouse Design**

```
📊 Star Schema (15 Tables)
├── 🔷 Dimension Tables (8)
│   ├── DimTime - Temporal analysis with date intelligence
│   ├── DimAsset - Property master data & characteristics
│   ├── DimFund - Fund structures & strategies
│   ├── DimInvestor - LP/GP relationships
│   ├── DimLender - Debt financing sources
│   ├── DimBorrower - Development partners
│   ├── DimMarket - Geographic markets & MSAs
│   └── DimPropertyManager - Operations teams
│
└── 📈 Fact Tables (7)
    ├── FactInvestment - Capital deployment & returns
    ├── FactAssetOperations - Property performance metrics
    ├── FactDebtIssued - Debt instruments & covenants
    ├── FactInvestorReturns - LP distributions & valuations
    ├── FactAssetSale - Property exits & proceeds
    ├── FactBudgetForecast - Forward projections
    └── FactBalanceSheet - Financial position
```

### **System Flow**

```
graph TB
    A[User: "Show multifamily properties with NOI > $1M"] --> B[Chat Interface]
    B --> C[Python Backend]
    C --> D[Conversation Memory]
    D --> E[GPT-4: SQL Generation]
    E --> F[Schema Validation]
    F --> G[SQL Server Execution]
    G --> H[Pandas Processing]
    H --> I[GPT-4: Business Insights]
    I --> J[Response Assembly]
    J --> K[Display Results]
    K --> L{User Action}
    L -->|Export| M[CSV/Excel/PDF Generator]
    L -->|Email| N[SMTP Delivery]
    L -->|Follow-up| D
```

### **Key Components**

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **portfolio_chat_agent.py** | Core AI logic & orchestration | Python, OpenAI GPT-4 |
| **server.py** | HTTP request handling | Python http.server |
| **chat_interface.html** | User interface | HTML5, JavaScript, CSS3 |
| **data_model.json** | Schema definitions & rules | JSON configuration |
| **enhanced_connection.py** | Database abstraction layer | pyodbc, connection pooling |

---

## 💡 Key Features Deep Dive

### **1. Schema-Aware SQL Generation**

The system loads your complete data model and generates SQL that:
- ✅ Respects dimension/fact relationships
- ✅ Uses proper join keys (integer date keys in YYYYMMDD format)
- ✅ Applies SQL Server-specific syntax (TOP not LIMIT)
- ✅ Validates against business rules before execution

**Example:**
```python
User: "Show me hospitality properties with debt maturing in Q1 2025"

Generated SQL:
SELECT 
    a.AssetName,
    a.City,
    d.CurrentBalance,
    d.MaturityDateKey
FROM DimAsset a
JOIN FactDebtIssued d ON a.AssetID = d.AssetID
WHERE a.PropertyType = 'Hospitality'
  AND d.MaturityDateKey BETWEEN 20250101 AND 20250331
  AND d.DebtStatus = 'Current'
ORDER BY d.MaturityDateKey
```

### **2. Business Intelligence Engine**

Automatically calculates real estate metrics:

| Metric | Formula | Business Use |
|--------|---------|--------------|
| **NOI** | Revenue - Operating Expenses | Property cash flow |
| **Cap Rate** | Annual NOI / Property Value | Valuation benchmark |
| **IRR** | Internal rate of return | Investment performance |
| **MOIC** | Total Value / Investment | Return multiple |
| **DSCR** | NOI / Debt Service | Loan covenant compliance |
| **LTV** | Loan / Property Value | Leverage analysis |

### **3. Conversation Memory**

The system remembers context across multiple turns:

```
User: "Show me all multifamily properties"
AI: [Returns 50 properties]

User: "Filter those to just Texas"
AI: [Remembers previous query, adds Texas filter]

User: "Sort by NOI descending"
AI: [Applies sort to filtered results]
```

### **4. Multi-Format Export Pipeline**

**CSV Export:** Raw data for analysis
- Headers with proper column names
- Number formatting preserved
- UTF-8 encoding

**Excel Export:** Formatted workbooks
- Auto-sized columns
- Number formatting ($, %, dates)
- Freeze panes on headers
- Professional styling

**PDF Reports:** Executive summaries
- Company branding
- Charts and visualizations
- Key metrics callouts
- Multi-page support

**Email Delivery:** Automated distribution
- Attachment in chosen format
- Customizable subject/body
- Recipient validation
- Delivery confirmation

---

## 📊 Sample Queries

### Portfolio Overview
```
"What property types do we have?"
"Show me all assets in California"
"List properties by acquisition price"
```

### Performance Analysis
```
"Which properties have NOI above $500k?"
"Show me occupancy rates by property type"
"What's the average cap rate for multifamily?"
```

### Debt Management
```
"Show me all debt maturing in 2025"
"Which properties have DSCR below 1.25?"
"What's our total outstanding debt?"
```

### Fund Analytics
```
"Give me IRR by fund"
"Show me total equity deployed by fund"
"Which funds have the highest returns?"
```

---

## 🎯 Business Use Cases

### **Fund Managers**
- Ad-hoc portfolio queries without SQL
- Quick answers for investor calls
- Automated quarterly reporting

### **Limited Partners (LPs)**
- Self-service investment performance tracking
- Capital call and distribution history
- Risk metric monitoring

### **Asset Managers**
- Property-level operational metrics
- Benchmark comparisons
- Budget vs. actual variance analysis

### **Debt Teams**
- Covenant compliance monitoring
- Refinancing opportunity identification
- Lender relationship tracking

### **Executives**
- High-level portfolio dashboards
- Board meeting materials
- Strategic planning data

---

## 🛡️ Security & Best Practices

### **Data Security**
- API keys stored in environment variables
- Database credentials never hardcoded
- Read-only database user for demo mode
- SQL injection prevention through parameterized queries

### **Rate Limiting**
- Maximum 10 queries per minute per user
- API call throttling to prevent abuse
- Cost monitoring for OpenAI API usage

### **Error Handling**
- Graceful failure for invalid queries
- User-friendly error messages
- Comprehensive logging for debugging

---

## 📈 Roadmap

### **Phase 1: Core Platform** ✅ Complete
- [x] Natural language to SQL translation
- [x] Conversation memory
- [x] Multi-format exports
- [x] Email delivery

### **Phase 2: Advanced Analytics** 🚧 In Progress
- [ ] Interactive charts and visualizations
- [ ] Predictive analytics (ML models)
- [ ] Scenario modeling
- [ ] Automated anomaly detection

### **Phase 3: Enterprise Features** 📋 Planned
- [ ] User authentication & authorization
- [ ] Role-based access control
- [ ] Audit logging
- [ ] API for external integrations
- [ ] Mobile app

---



### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black .
flake8 .
```

---



---

## 📧 Contact

**Maniteja Kurukunda**
- Email: manitejakurukunda@gmail.com

---

## 🙏 Acknowledgments

- OpenAI GPT-4 for natural language understanding
- Real estate domain experts for business rule validation
- Open source community for excellent Python libraries


---

**⭐ Star this repo if you found it helpful!**
