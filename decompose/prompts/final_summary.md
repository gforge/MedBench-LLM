Please create a discharge summary based on the following already partially summarized information enclosed in triple quotes:

"""
{preprocessed_information}
"""

Format the discharge summary as follows (use discharg_summary tag for delimiting the summary):

<discharge_summary>
# Main diagnosis
[Primary diagnosis with ICD code, e.g. Primary Knee Osteoarthritis (M17.1)]

# Secondary diagnosis
[Secondary diagnosis with ICD code, e.g. Hypertension (I10)]

# Procedures
[If applicable, provide a bullet-point list of procedures. Include: Procedure name, date, and surgeon. Example:

- Total Knee Arthroplasty, 2023-08-15, Dr. Jane Smith]

# Reason for admission
[Provide a brief, focused description of why the patient was admitted.]

# Medical history
[Include only the medical history directly relevant to the current admission. Omit unrelated conditions.]

# Social history
[Include only social history that directly impacts current care or follow-up. Examples: smoking status for respiratory issues, living situation for discharge planning.]

# Hospital course
[Write in narrative style, focusing on:

-   Significant occurrences
-   Changes in condition
-   Treatment milestones
-   Key laboratory or imaging findings Organize chronologically. Use clear topic sentences for each paragraph. End with the patient's discharge destination if available.

Example: "Patient developed postoperative fever, peaking at 38.4°C on day 2. CRP levels increased to a maximum of 312 mg/L on postoperative day 3, then gradually decreased without antibiotic administration. This was interpreted as a normal postoperative inflammatory response. The patient was discharged home on postoperative day 5."]

# Medication changes
[List in bullet points:

-   New medications (with dosage and frequency)
-   Discontinued medications
-   Modified dosages of existing medications Do not include temporary medications discontinued at discharge (e.g., IV antibiotics, perioperative medications).]

# Plan
[Provide a bullet-point list including:

-   Follow-up appointments (with specific dates if available)
-   Specific instructions or precautions for the patient
-   Any pending tests or studies]
</discharge_summary>

Additional guidelines for this discharge summary:
1. Limit the Hospital Course to a maximum of 3 paragraphs, each with 3-5 sentences, unless the case is particularly complex.
2. Use ICD-10 codes for all diagnoses.
3. Ensure the summary is comprehensive yet concise, focusing on information critical for continuity of care.
4. If any section cannot be completed due to lack of information in the notes, write "Not reported" for that section.
5. For medications use thrice daily instead of 1+1+1, or in the evening instead of 0+0+1 whenever possible.

Please generate the discharge summary based on these instructions and the provided clinical notes.