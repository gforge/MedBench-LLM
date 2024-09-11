You are responsible for extracting the important entities in the <note>.

First extract all main diagnosis and it's corresponding diagnosis code, then extract all secondary diagnosis (other medical conditions that are not the main diagnosis for admission), then extract the social history of the patient, then extract all the medical condition that patient has before admission (including any chronic diseases, surgeries, significant illnesses and treatment plans a patient may have had), finally extract the reasons for admission.

Desired format:
Main diagnosis: <comma_separated_list_of_main_diagnosis_name_with_diagnosis_code_in parentheses>
Secondary diagnosis: <comma_separated_list_of_secondary_diagnosis_name_with_diagnosis_code_in parentheses>
Social history: <comma_separated_list_of_all_social_history>
Past medical history: <comma_separated_list_of_all_medical_condition_before_admission>
Reasons for admission: <comma_separated_list_of_the_main_reason_for_admission>

Note: ###
{note}
###

Return the output in Markdown format.