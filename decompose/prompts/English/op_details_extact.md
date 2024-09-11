You are responsible for extracting the important entities in the note.

First extract all the surgery procedures underwent, then extract the date that correspond to each procedure, then extract the corresponding surgeons who conducted each procedure, and finally sum up the number of surgeries performed to get the total number of surgery performed.

Desired format:
Surgery details:
Total no of procedures: <total_number_of_surgeries_performed>

For each surgery procedure:
    - Name of procedures, Date of surgery, Surgeon(s)

Note: ###
{note}
###

Return the output in markdown format.