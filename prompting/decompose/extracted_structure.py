# Organised the extracted output in a structure format
extracted_functions = [{
    "name": "Extraction",
    "description": "All extracted information from the documents",
    "parameters": {
        "type": "object",
        "properties": {
            "main diagnosis": {
                "type": "string",
                "description": "the main diagnosis that leads to the admission"
            },
            "main diagnosis code": {
                "type":
                "string",
                "description":
                "the main diagnosis code that leads to the admission"
            },
            "co-existing conditions": {
                "type":
                "string",
                "description":
                "all co-existing conditions that the patient has at the point of admission"
            },
            "social history": {
                "type": "string",
                "description": "social history of the patient"
            },
            "past medical history": {
                "type":
                "string",
                "description":
                "patient's health status before admission including any chronic diseases, surgeries, significant"
                + " illnesses and treatment plans a patient may have had"
            },
            "admission reasons": {
                "type":
                "string",
                "description":
                "detailed description of the reasons for current admission"
            },
            "clinical findings": {
                "type": "string",
                "description":
                "all significant clinical findings on examination"
            }
        }
    }
}]
