# 🏥 CDSS - Clinical Decision Support System

**AI-Based Medical Error Risk Prediction System**

An intelligent web-based Clinical Decision Support System that uses Machine Learning to predict medical error risk and provide meaningful, low-fatigue alerts to healthcare professionals.

---

## 🌟 Features

- **ML-Based Risk Prediction**: Uses Random Forest, Logistic Regression, or Decision Tree models
- **Symptom-Driven Analysis**: Analyzes patient symptoms, vital signs, and medical history
- **Smart Alert System**: Reduces alert fatigue by only showing alerts for medium/high risk cases
- **Interactive Web UI**: Built with Streamlit for easy use by non-technical users
- **Visual Risk Assessment**: Gauge charts, probability distributions, and feature importance
- **Clinical Recommendations**: Provides actionable recommendations based on risk level

---

## 📁 Project Structure

```
cdss-risk-prediction-system/
├── app/
│   ├── main.py                    # Streamlit application
│   ├── components/
│   │   ├── input_form.py          # Patient input forms
│   │   ├── risk_display.py        # Risk visualization
│   │   └── alert_component.py     # Alert display
│   └── utils/
│       └── validators.py          # Input validation
├── ml/
│   ├── preprocessing.py           # Data preprocessing
│   ├── feature_encoder.py         # Feature encoding
│   ├── model.py                   # ML model training/inference
│   └── risk_classifier.py         # Risk classification engine
├── data/
│   └── generate_data.py           # Sample data generator
├── models/                        # Saved trained models
├── tests/                         # Unit tests
├── config.py                      # Configuration settings
├── requirements.txt               # Dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cdss-risk-prediction-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Sample Data & Train Model

```bash
python data/generate_data.py
python -m ml.model
```

### 5. Run the Application

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📊 How It Works

### System Flow

```
Patient Data Input → Data Validation → Feature Encoding → ML Model Prediction
                                                                ↓
Clinical Recommendations ← Alert Generation ← Risk Classification
```

### Risk Levels

| Level | Probability | Alert | Color |
|-------|-------------|-------|-------|
| **Low** | < 30% | No alert | 🟢 Green |
| **Medium** | 30-60% | Warning | 🟡 Yellow |
| **High** | > 60% | Critical | 🔴 Red |

---

## 🧪 Testing

Run all tests:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_risk_classifier.py -v
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

- Risk thresholds
- Alert settings
- Symptom lists
- Vital sign ranges
- UI configuration

---

## 📖 Usage Guide

### For Healthcare Professionals

1. **Enter Patient Demographics**: Age and gender
2. **Select Symptoms**: Check all symptoms the patient is experiencing
3. **Input Vital Signs**: Heart rate, blood pressure, temperature, etc.
4. **Add Medical History**: Pre-existing conditions
5. **Click "Analyze Risk"**: View the AI-generated risk assessment

### Interpreting Results

- **Risk Gauge**: Shows overall risk score (0-100%)
- **Risk Badge**: Large colored indicator of risk level
- **Probability Chart**: Shows likelihood of each risk level
- **Alerts**: Only shown for medium/high risk (reduces alert fatigue)
- **Recommendations**: Clinical actions based on risk level

---

## 🔬 ML Model Details

### Features Used

- **Demographics**: Age, gender
- **Symptoms**: 12 symptoms including fever, cough, chest pain, confusion
- **Vital Signs**: Heart rate, blood pressure, temperature, SpO2, respiratory rate
- **Medical History**: 6 pre-existing conditions

### Algorithms

- **Random Forest** (default): Best balance of accuracy and interpretability
- **Logistic Regression**: Good for understanding feature weights
- **Decision Tree**: Most interpretable, visual decision paths

---

## ⚠️ Disclaimer

> **This is an educational/demonstration project.**
> 
> This system is a decision support tool and does **NOT** replace clinical judgment. 
> It uses synthetic data for training and should not be used for actual medical decisions.
> Always consult qualified healthcare professionals for medical advice.

---

## 📝 License

This project is for educational purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📧 Contact

For questions or suggestions, please open an issue in the repository.
