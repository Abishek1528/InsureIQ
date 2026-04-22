# InsureIQ — Insurance Recommendation System PRD

## 1. Target User

* Age: 30–50 years  
* Segment: Middle-class Indian households  
* Family: Married, 1–2 children, possibly dependent parents  
* Income: ₹5L – ₹20L annually  

### Behavioral Traits
* Price-sensitive but risk-aware  
* Avoids complex financial decisions  
* Relies on agents, friends, or quick online searches  
* Rarely reads full policy documents  

### Decision Pattern
* Compares plans primarily on premium  
* Chooses “safe-looking” or commonly recommended plans  
* Does not evaluate exclusions, waiting periods, or hospital network in depth  

---
## 2. Primary Pain Points

### 1. Inability to Understand Policies
* Users cannot interpret terms like “co-pay”, “deductible”, “waiting period”, or “room rent cap”  
* As a result, they compare plans only on premium, ignoring critical limitations  
* Example: A user selects a low-premium plan without realizing a 20% co-pay applies to every claim  

---

### 2. Fear of Claim Rejection
* Users are highly anxious about hidden clauses and exclusions  
* Lack of clarity on what is actually covered creates mistrust  
* Example: A user purchases a policy assuming full coverage, but later discovers pre-existing conditions like diabetes are excluded for 2–3 years  

---

### 3. Decision Paralysis Due to Overchoice
* Multiple plans appear similar with no clear differentiation  
* Users lack a framework to evaluate trade-offs (premium vs coverage vs waiting period)  
* This leads to either delaying the decision or choosing a random/recommended plan  

---

### 4. Misaligned Plan Selection
* Users often optimize for lowest premium instead of adequate coverage  
* Key factors like waiting periods, sub-limits, and exclusions are ignored  
* Example: A user selects a cheaper plan but faces high out-of-pocket costs due to room rent limits during hospitalization  

---

### 5. Lack of Trust and Transparency
* Users believe insurers may reject claims using fine print  
* Recommendations from agents are seen as biased or commission-driven  
* This reduces confidence in making independent decisions  

---

### 6. Uncertainty Around Hospital Network
* Users do not know if nearby or preferred hospitals are covered under a plan  
* This becomes critical only during emergencies, when switching is not possible  
* Example: A user realizes their nearest hospital is not part of the insurer’s network at the time of claim  

---
## 3. Feature Prioritisation with Rationale

### Must-Have (MVP)

1. Recommendation Engine  
   - Suggests top 2–3 plans based on user profile  
   - Prioritized because users are unable to independently evaluate multiple plans  

2. Structured User Input Form  
   - Inputs: age, income, city, family size, pre-existing diseases  
   - Enables personalization instead of generic recommendations  

3. Simplified Policy Explanation  
   - Converts technical terms into plain language  
   - Critical to build trust and reduce confusion  

4. Focused Comparison View  
   - Displays only key factors:
     - Premium  
     - Coverage  
     - Waiting period  
     - Hospital network  
   - Prevents information overload and improves clarity  

---

### Good-to-Have

* Risk indicators (e.g., likelihood of claim issues)  
* Personalized warnings (e.g., disease not covered immediately)  
* Premium vs coverage trade-off visualization  

---

### Future Features

* Integration with real insurer APIs  
* Claim assistance and support system  
* Dynamic recommendations based on user health updates  

---

## 4. Recommendation Logic

The system uses a rule-based filtering and scoring approach to match users with suitable insurance plans.

### Input Parameters

* Age  
* Income  
* City  
* Family size  
* Pre-existing diseases  

---

### Step 1: Filtering

Remove plans that:
* Do not cover relevant pre-existing diseases  
* Have long waiting periods for critical conditions  
* Are not applicable for the user’s age group  

---

### Step 2: Scoring

Each remaining plan is evaluated across four dimensions:

1. Affordability  
   - Premium relative to user income  
   - High premium plans penalized for low-income users  

2. Coverage Adequacy  
   - Higher coverage preferred for larger families  
   - Lower coverage penalized for high-risk users  

3. Waiting Period Risk  
   - Plans with long waiting periods penalized for users with pre-existing conditions  
   - Older users prioritized for shorter waiting periods  

4. Hospital Network Relevance  
   - Plans with strong network in user’s city ranked higher  
   - Weak local coverage reduces score  

---

### Step 3: Trade-off Handling

* Lower premium vs higher coverage:
  - Lower-income users → prioritize affordability  
  - Higher-income users → prioritize coverage  

* Low premium vs long waiting period:
  - Penalized heavily for users with existing health risks  

---

### Step 4: Ranking & Output

* Aggregate score calculated for each plan  
* Top 2–3 plans recommended  
* Each recommendation includes a clear reason:
  - Example: “Recommended due to low waiting period and strong hospital network in your city”  

---

## 5. Assumptions

### Domain Assumptions

* Insurance plans can be represented with structured attributes:
  - Premium, coverage, waiting period, hospital network  
* Real-time insurer APIs are not available; static/mock data is used  

---

### User Behavior Assumptions

* Users do not read detailed policy documents  
* Users prefer simple explanations over technical details  
* Trust increases when recommendations include clear reasoning  
* Users prefer 2–3 strong options rather than many choices  
* Users value clarity and transparency over exhaustive comparison  

---

## Summary

This system focuses on simplifying insurance decision-making by:

* Reducing confusion through structured recommendations  
* Building trust via transparent explanations  
* Matching users to plans based on both financial and health factors  

The core value lies in guiding users to the most suitable plan with clear reasoning, rather than overwhelming them with choices.