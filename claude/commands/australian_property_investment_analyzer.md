# Australian Property Investment Analyzer Command

## Purpose
Comprehensive property investment analysis specifically designed for Australian real estate market, focusing on Perth and Australian capital city markets with detailed cash flow, tax, and capital growth analysis.

## Usage
"Analyze property investment opportunity" or "Property investment feasibility study" or "Real estate investment analysis"

## Inputs
- Property details (location, price, type, condition)
- Rental income estimates or current rental
- Purchase costs (stamp duty, legal, inspection, loan fees)
- Ongoing costs (rates, insurance, maintenance, property management)
- Financing details (loan amount, interest rate, loan term)
- Personal financial position (income, tax bracket, other investments)
- Investment timeline and exit strategy
- Market research data for the area

## Outputs
- Comprehensive property investment analysis report
- Cash flow projections (positive/negative gearing analysis)
- Tax benefits and deduction calculations
- Capital growth projections and total return estimates
- Risk assessment and sensitivity analysis
- Comparative analysis vs other investment options
- Financing strategy recommendations
- Implementation timeline and action plan

## Implementation

### 1. Market Analysis & Due Diligence
```
- Suburb analysis and demographic trends
- Recent sales data and price trends
- Rental yield analysis and vacancy rates
- Infrastructure development and growth drivers
- Supply and demand dynamics
- Capital city comparison and Perth-specific factors
```

### 2. Financial Analysis Framework
```
- Purchase price and acquisition cost analysis
- Rental income estimation and yield calculations
- Operating expense breakdown and projections
- Net cash flow analysis (before and after tax)
- Break-even analysis and cash flow breakeven point
- Return on investment calculations (gross/net yield, total return)
```

### 3. Tax Analysis & Optimization
```
- Negative gearing benefits and tax deductions
- Depreciation schedule analysis and benefits
- Capital gains tax implications and optimization
- Interest deductibility and loan structuring
- Property-related expense deductions
- Land tax implications and optimization strategies
```

### 4. Capital Growth Analysis
```
- Historical capital growth rates for area
- Future growth drivers and catalysts
- Infrastructure impact on property values
- Population growth and demographic shifts
- Comparative analysis with other Perth suburbs
- Long-term capital appreciation projections
```

### 5. Risk Assessment & Scenario Analysis
```
- Interest rate sensitivity analysis
- Vacancy risk and rental market analysis
- Property value volatility and market risk
- Liquidity risk and exit strategy assessment
- Maintenance and capital expenditure risks
- Legislative and tax policy change impacts
```

### 6. Financing Strategy Optimization
```
- Optimal loan structure and loan-to-value ratio
- Fixed vs variable interest rate analysis
- Offset account and redraw facility optimization
- Interest-only vs principal and interest comparison
- Loan splitting strategies for tax optimization
- Refinancing and ongoing optimization opportunities
```

## Australian Property Market Framework

### Perth Market Analysis
```python
# Perth property market characteristics
perth_market_data = {
    'median_house_price': 650000,      # Approximate median (varies by area)
    'rental_yields': {'houses': 0.045, 'units': 0.055},
    'vacancy_rates': 0.015,            # Current vacancy rates
    'capital_growth_5yr': 0.02,        # Average annual growth
    'stamp_duty_rate': 'WA_rates',     # State-specific stamp duty
    'land_tax_threshold': 300000,      # WA land tax threshold
    'key_growth_areas': ['Cockburn', 'Wanneroo', 'Joondalup', 'Rockingham']
}
```

### Australian Tax Framework for Property
```python
# Property investment tax calculations
def property_tax_analysis():
    """
    Calculate tax implications of property investment
    """
    deductions = {
        'interest': 'loan_interest_on_investment_portion',
        'depreciation': {'building': 0.025, 'fixtures': 0.10_0.20},  # Annual rates
        'maintenance': 'repairs_and_maintenance_immediate_deduction',
        'property_management': 'typically_7_10_percent_of_rent',
        'insurance': 'building_and_contents_insurance',
        'rates': 'council_and_water_rates',
        'advertising': 'tenant_advertising_costs',
        'legal_accounting': 'professional_services'
    }
    return tax_benefit_calculation
```

### Stamp Duty Calculations by State
```python
# Australian stamp duty calculator
def stamp_duty_calculator(property_value, state, first_home_buyer=False):
    """
    Calculate stamp duty based on state and property value
    """
    wa_rates = [
        (120000, 0.015),    # 1.5% up to $120k
        (150000, 0.025),    # 2.5% from $120k to $150k
        (360000, 0.035),    # 3.5% from $150k to $360k
        (725000, 0.045),    # 4.5% from $360k to $725k
        (float('inf'), 0.055)  # 5.5% above $725k
    ]
    # Apply first home buyer concessions if applicable
    return calculated_stamp_duty
```

## Detailed Investment Analysis

### Cash Flow Analysis
```python
# Comprehensive cash flow modeling
def property_cash_flow_analysis(purchase_price, rental_income, expenses, financing):
    """
    Model property investment cash flows over investment period
    """
    # Acquisition costs
    acquisition_costs = {
        'stamp_duty': calculate_stamp_duty(purchase_price),
        'legal_fees': purchase_price * 0.001,  # Approximately 0.1%
        'building_inspection': 500,
        'loan_fees': 1000,
        'other_costs': 2000
    }
    
    # Annual operating expenses
    annual_expenses = {
        'council_rates': rental_income * 0.05,   # Typical percentage
        'water_rates': 800,                      # Annual estimate
        'insurance': 1200,                       # Building insurance
        'property_management': rental_income * 0.08,
        'maintenance': rental_income * 0.05,     # Maintenance reserve
        'land_tax': calculate_land_tax(purchase_price),
        'loan_interest': financing['loan_amount'] * financing['interest_rate']
    }
    
    return cash_flow_projection
```

### Negative Gearing Benefits
```python
# Negative gearing tax benefit calculation
def negative_gearing_analysis(rental_income, deductible_expenses, marginal_tax_rate):
    """
    Calculate tax benefits from negative gearing
    """
    net_rental_loss = deductible_expenses - rental_income
    if net_rental_loss > 0:
        tax_savings = net_rental_loss * marginal_tax_rate
        after_tax_cost = net_rental_loss - tax_savings
        return {
            'rental_loss': net_rental_loss,
            'tax_savings': tax_savings,
            'after_tax_cost': after_tax_cost,
            'effective_cost_reduction': tax_savings / net_rental_loss
        }
```

### Depreciation Benefits Analysis
```python
# Property depreciation tax benefits
def depreciation_analysis(property_details):
    """
    Calculate depreciation deductions for property investment
    """
    depreciation_schedule = {
        'building_allowance': {
            'rate': 0.025,  # 2.5% for buildings constructed after 1987
            'eligible_value': property_details['building_value']
        },
        'plant_equipment': {
            'rate_range': (0.10, 0.33),  # 10-33% depending on item
            'items': ['carpets', 'blinds', 'air_conditioning', 'hot_water']
        }
    }
    
    # Calculate annual depreciation deductions
    annual_depreciation = calculate_total_depreciation(depreciation_schedule)
    tax_benefit = annual_depreciation * marginal_tax_rate
    return depreciation_benefits
```

## Perth-Specific Market Intelligence

### Growth Area Analysis
```python
# Perth growth corridor analysis
def perth_growth_areas():
    """
    Analyze Perth's key growth areas and investment opportunities
    """
    growth_areas = {
        'north_corridor': {
            'suburbs': ['Wanneroo', 'Joondalup', 'Mindarie'],
            'drivers': ['population_growth', 'infrastructure_development'],
            'median_price': 550000,
            'rental_yield': 0.048,
            'growth_potential': 'high'
        },
        'south_corridor': {
            'suburbs': ['Cockburn', 'Baldivis', 'Rockingham'],
            'drivers': ['employment_growth', 'transport_links'],
            'median_price': 480000,
            'rental_yield': 0.052,
            'growth_potential': 'medium_high'
        },
        'hills_corridor': {
            'suburbs': ['Ellenbrook', 'Aveley', 'The Vines'],
            'drivers': ['lifestyle_demand', 'airport_proximity'],
            'median_price': 420000,
            'rental_yield': 0.055,
            'growth_potential': 'medium'
        }
    }
    return growth_area_analysis
```

### Infrastructure Impact Analysis
```python
# Infrastructure development impact on property values
def infrastructure_impact_analysis(suburb):
    """
    Analyze how infrastructure developments affect property investment
    """
    infrastructure_projects = {
        'metronet': {
            'impact_suburbs': ['Ellenbrook', 'Morley', 'Belmont'],
            'completion': '2025-2030',
            'expected_uplift': '10-15%'
        },
        'westport': {
            'impact_areas': ['Kwinana', 'Rockingham', 'Baldivis'],
            'timeline': '2030+',
            'expected_impact': 'employment_growth'
        },
        'perth_city_link': {
            'impact_areas': ['Northbridge', 'East_Perth', 'Perth_CBD'],
            'status': 'completed',
            'ongoing_benefit': 'connectivity_premium'
        }
    }
    return infrastructure_analysis
```

## Risk Analysis & Scenario Modeling

### Interest Rate Sensitivity Analysis
```python
# Interest rate impact on property investment returns
def interest_rate_sensitivity(base_scenario, rate_changes):
    """
    Analyze impact of interest rate changes on investment viability
    """
    scenarios = {}
    for rate_change in rate_changes:
        new_rate = base_scenario['interest_rate'] + rate_change
        new_interest_cost = base_scenario['loan_amount'] * new_rate
        cash_flow_impact = base_scenario['interest_cost'] - new_interest_cost
        scenarios[f'rate_+{rate_change}%'] = {
            'new_interest_cost': new_interest_cost,
            'cash_flow_change': cash_flow_impact,
            'break_even_rent': calculate_break_even_rent(new_interest_cost)
        }
    return scenarios
```

### Market Downturn Analysis
```python
# Property market downturn scenario analysis
def market_downturn_scenarios(property_value, loan_amount):
    """
    Analyze impact of various market downturn scenarios
    """
    downturn_scenarios = {
        'mild_correction': -0.10,      # 10% price decline
        'moderate_correction': -0.20,   # 20% price decline
        'severe_correction': -0.30      # 30% price decline
    }
    
    for scenario, decline in downturn_scenarios.items():
        new_value = property_value * (1 + decline)
        equity_position = new_value - loan_amount
        lvr = loan_amount / new_value if new_value > 0 else float('inf')
        
        scenarios[scenario] = {
            'new_property_value': new_value,
            'equity_position': equity_position,
            'loan_to_value': lvr,
            'margin_call_risk': 'high' if lvr > 0.90 else 'low'
        }
    return scenarios
```

## Comparative Investment Analysis

### Property vs Other Investments
```python
# Compare property investment with alternatives
def investment_comparison_analysis():
    """
    Compare property investment returns with other asset classes
    """
    investment_options = {
        'property_direct': {
            'expected_return': 0.08,     # Capital growth + rental yield
            'tax_benefits': 'negative_gearing_depreciation',
            'liquidity': 'low',
            'entry_cost': 'high',
            'management': 'active'
        },
        'property_reits': {
            'expected_return': 0.07,
            'tax_benefits': 'franking_credits',
            'liquidity': 'high',
            'entry_cost': 'low',
            'management': 'passive'
        },
        'asx_shares': {
            'expected_return': 0.09,
            'tax_benefits': 'franking_credits_cgt_discount',
            'liquidity': 'high',
            'entry_cost': 'low',
            'management': 'varies'
        },
        'term_deposits': {
            'expected_return': 0.04,
            'tax_benefits': 'none',
            'liquidity': 'medium',
            'entry_cost': 'nil',
            'management': 'passive'
        }
    }
    return comparison_matrix
```

## Implementation & Due Diligence

### Property Selection Criteria
```python
# Investment property selection framework
def property_selection_criteria():
    """
    Framework for evaluating potential investment properties
    """
    selection_criteria = {
        'location_factors': {
            'proximity_to_transport': 'within_1km_public_transport',
            'proximity_to_employment': 'major_employment_hubs',
            'school_zones': 'quality_primary_secondary',
            'amenities': 'shopping_medical_recreation',
            'demographics': 'stable_growing_population'
        },
        'property_factors': {
            'land_to_asset_ratio': 'minimum_30_percent_land',
            'rental_demand': 'strong_tenant_demand',
            'condition': 'good_condition_minimal_work_required',
            'unique_features': 'parking_outdoor_space_storage',
            'development_potential': 'subdivision_renovation_opportunity'
        },
        'financial_factors': {
            'rental_yield': 'minimum_4_percent',
            'purchase_below_market': 'target_5_10_percent_discount',
            'growth_potential': 'historical_3_percent_annual',
            'affordability': 'within_budget_serviceability'
        }
    }
    return selection_framework
```

### Due Diligence Checklist
```python
# Comprehensive due diligence process
def due_diligence_checklist():
    """
    Complete due diligence checklist for property investment
    """
    checklist = {
        'legal_compliance': [
            'title_search_clear_title',
            'council_approvals_compliance',
            'heritage_overlays_restrictions',
            'easements_encumbrances',
            'zoning_future_development_rights'
        ],
        'physical_inspection': [
            'building_pest_inspection',
            'structural_integrity_assessment',
            'electrical_plumbing_systems',
            'roof_condition_age',
            'renovation_requirements_costs'
        ],
        'financial_verification': [
            'rental_appraisal_market_rent',
            'comparable_sales_analysis',
            'council_water_rates',
            'strata_fees_if_applicable',
            'insurance_quotes'
        ],
        'market_analysis': [
            'suburb_growth_trends',
            'rental_vacancy_rates',
            'future_development_supply',
            'infrastructure_projects',
            'demographic_analysis'
        ]
    }
    return checklist
```

## Reporting & Decision Framework

### Investment Analysis Report Structure
1. **Executive Summary**: Key metrics, recommendation, and rationale
2. **Market Analysis**: Suburb analysis, trends, and growth drivers
3. **Financial Analysis**: Cash flow, returns, and tax benefits
4. **Risk Assessment**: Scenario analysis and risk mitigation
5. **Comparative Analysis**: Property vs alternative investments
6. **Implementation Plan**: Purchase process and ongoing management
7. **Exit Strategy**: Long-term hold vs disposal considerations

### Decision Matrix
```python
# Property investment decision framework
def investment_decision_matrix(analysis_results):
    """
    Systematic decision framework for property investment
    """
    decision_factors = {
        'financial_metrics': {
            'gross_yield': {'weight': 0.20, 'threshold': 0.045},
            'net_yield': {'weight': 0.15, 'threshold': 0.035},
            'capital_growth': {'weight': 0.25, 'threshold': 0.03},
            'total_return': {'weight': 0.20, 'threshold': 0.08}
        },
        'location_quality': {
            'transport_access': {'weight': 0.10, 'score_out_of': 10},
            'amenities': {'weight': 0.05, 'score_out_of': 10},
            'demographics': {'weight': 0.05, 'score_out_of': 10}
        }
    }
    
    # Calculate weighted score and investment recommendation
    return investment_recommendation
```

### Performance Monitoring Framework
- **Monthly Monitoring**: Cash flow tracking, rent collection, expenses
- **Quarterly Reviews**: Market value updates, rental market assessment
- **Annual Analysis**: Tax benefit realization, strategy review
- **Triennial Review**: Major strategic assessment, hold vs sell decision

This Australian Property Investment Analyzer provides comprehensive analysis specifically designed for the Australian real estate market, with particular focus on Perth market dynamics, Australian tax legislation, and investment optimization strategies for high-income earners.