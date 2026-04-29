# Task
Create a discharge summary from the clinical notes below:
```
{notes}
```

Follow the structure below:

## Primary diagnosis
Primary diagnosis with ICD-10 code
*Example: Primary knee osteoarthritis (M17.1)*

## Secondary Diagnoses
List secondary diagnoses with ICD-10 codes

## Procedure Codes
Bullet list with KVÅ code followed by procedure description, e.g. NFJ59 Osteosynthesis with intramedullary nail

## Reason for Admission
State the confirmed injury/diagnosis that led to admission in a few words

## Medical History
Include only history relevant to the current admission

## Hospital Course
Be concise and focus on making it easy to read for a physician, including the following:
- What happened during the stay
- Important changes in the patient’s condition
- Treatment progress and key findings
- Conclude with discharge destination
- Explain in continuous text
*Example: "The patient developed fever after surgery, reaching 38.4°C on day 2. CRP levels increased to a peak of 312 mg/L three days postoperatively and then gradually decreased without antibiotic treatment. This was interpreted as a normal postoperative inflammatory response. The patient was discharged five days after surgery to their usual residence."*

## Medications
**New medications:**
- Name, dose, frequency (write "twice daily" not "1x2", "three times daily" not "1+1+1")
**Discontinued medications:**
- List stopped medications
**Changed medications:**
- Note dose changes
*Skip temporary medications that have been discontinued at discharge (e.g. IV antibiotics, perioperative medications)*

### Plan
- Follow-up visits (include specific dates if available)
- Specific instructions for the patient
- Any pending investigations or studies
