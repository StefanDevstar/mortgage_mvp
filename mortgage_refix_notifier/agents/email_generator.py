# agents/client_email_generator.py

from jinja2 import Template
from datetime import datetime

# ── Draft Broker Email Template ───────────────────────────────────────────────────────
DRAFT_BROKER_EMAIL_TMPL = Template("""\
Hi {{ first_name }}!

Hope you’re doing well.  
I’m reaching out about your {{ bank_name }} home loan, which is coming up for refix in {{ days_until_expiry }} days (on {{ expiry_date }}).

Your {{ bank_name }} loan details:
{% for f in facilities %}
- {{ f.name }}: ${{ f.balance | round(2) }} — action required
{% endfor %}

Estimated property valuation: ${{ valuation.estimated_value | round(2) }} (as of {{ valuation.valuation_date }})

We can request updated rates from {{ bank_name }} to make sure you get the best deal—and guide you through the refix process.  

Please let us know how you’d like to proceed.

Kind regards,  
{{ advisor_name }}
""")
# ── First Email Template ───────────────────────────────────────────────────────
FIRST_EMAIL_TMPL = Template("""\
Hi {{ first_name }}!

Hope you’re doing well.  
I’m reaching out about your {{ bank_name }} home loan, which is coming up for refix in {{ days_until_expiry }} days (on {{ expiry_date }}).

Your {{ bank_name }} loan details:
{% for f in facilities %}
- {{ f.name }}: ${{ f.balance | round(2) }} — action required
{% endfor %}

Estimated property valuation: ${{ valuation.estimated_value | round(2) }} (as of {{ valuation.valuation_date }})

We can request updated rates from {{ bank_name }} to make sure you get the best deal—and guide you through the refix process.  

Please let us know how you’d like to proceed.

Kind regards,  
{{ advisor_name }}
""")

# ── Second Email Template ──────────────────────────────────────────────────────
SECOND_EMAIL_TMPL = Template("""\
Hi {{ first_name }}!

Great to see your response. As discussed, here are your current facilities up for refix:
{% for f in facilities %}
- {{ f.name }}: ${{ f.balance | round(2) }}
{% endfor %}

**Rate offers**  
{% for term, rate in rates.items() %}
- {{ term }}: {{ rate }}%
{% endfor %}

**Repayment scenarios** (Principal & Interest, weekly)  
{% for term, weekly in repayment.items() %}
- {{ term }}: ${{ weekly | round(2) }}
{% endfor %}

**Breakeven analysis**  
Months{% for m in breakeven.months %} | {{ m }}{% endfor %}
Rates{% for r in breakeven.rates %} | {{ r }}%{% endfor %}

**Recommended loan structures**  
{% for rec in recommendations %}
- {{ rec }}
{% endfor %}

**Market insights**  
{% for insight in insights %}
- {{ insight }}
{% endfor %}

Next steps: reply to this email or contact me at {{ advisor_email }} when you’re ready to move forward.

Kind regards,  
{{ advisor_name }}
""")

def draft_broker_email(job) -> str:
    return DRAFT_BROKER_EMAIL_TMPL.render()

def draft_client_followup(
    first_name: str,
    bank_name: str,
    expiry_date: datetime,
    facilities: list[dict],
    valuation: dict,
    advisor_name: str
) -> str:
    """
    Generate the first refix reminder email to go to the CLIENT.
    
    - first_name: client's first name
    - bank_name: e.g. "ASB"
    - expiry_date: datetime of fixed term expiry
    - facilities: list of dicts, each with 'name' and 'balance'
    - valuation: dict with 'estimated_value' and 'valuation_date'
    - advisor_name: name to sign off with
    """
    days_until = (expiry_date.date() - datetime.utcnow().date()).days
    return FIRST_EMAIL_TMPL.render(
        first_name=first_name,
        bank_name=bank_name,
        days_until_expiry=days_until,
        expiry_date=expiry_date.date().isoformat(),
        facilities=facilities,
        valuation=valuation,
        advisor_name=advisor_name
    )
def generate_first_email(
    first_name: str,
    bank_name: str,
    expiry_date: datetime,
    facilities: list[dict],
    valuation: dict,
    advisor_name: str
) -> str:
    """
    Generate the first refix reminder email to go to the CLIENT.
    
    - first_name: client's first name
    - bank_name: e.g. "ASB"
    - expiry_date: datetime of fixed term expiry
    - facilities: list of dicts, each with 'name' and 'balance'
    - valuation: dict with 'estimated_value' and 'valuation_date'
    - advisor_name: name to sign off with
    """
    days_until = (expiry_date.date() - datetime.utcnow().date()).days
    return FIRST_EMAIL_TMPL.render(
        first_name=first_name,
        bank_name=bank_name,
        days_until_expiry=days_until,
        expiry_date=expiry_date.date().isoformat(),
        facilities=facilities,
        valuation=valuation,
        advisor_name=advisor_name
    )

def generate_second_email(
    first_name: str,
    bank_name: str,
    facilities: list[dict],
    rates: dict,
    repayment: dict,
    breakeven: dict,
    recommendations: list[str],
    insights: list[str],
    advisor_name: str,
    advisor_email: str
) -> str:
    """
    Generate the detailed follow-up email after CLIENT response.
    
    - facilities: as above
    - rates: dict mapping term -> rate (float)
    - repayment: dict mapping term -> weekly payment (float)
    - breakeven: dict with 'months': list[int], 'rates': list[float]
    - recommendations: list of strings
    - insights: list of market commentary strings
    - advisor_name/email: for sign-off and contact
    """
    return SECOND_EMAIL_TMPL.render(
        first_name=first_name,
        bank_name=bank_name,
        facilities=facilities,
        rates=rates,
        repayment=repayment,
        breakeven=breakeven,
        recommendations=recommendations,
        insights=insights,
        advisor_name=advisor_name,
        advisor_email=advisor_email
    )
