Du är ansvarig för att extrahera de viktiga enheterna i <anteckning>.

Först, extrahera alla huvuddiagnoser och deras motsvarande diagnoskoder, sedan extrahera alla sekundära diagnoser (andra medicinska tillstånd som inte är huvuddiagnosen för inläggning), därefter extrahera patientens sociala historia, sedan extrahera alla medicinska tillstånd som patienten har före inläggningen (inklusive eventuella kroniska sjukdomar, operationer, betydande sjukdomar och behandlingsplaner som patienten kan ha haft), och slutligen extrahera orsakerna till inläggningen.

Önskat format:
Huvuddiagnos: <kommaseparerad_lista_av_huvuddiagnos_namn_med_diagnoskod_i_parentes>
Sekundär diagnos: <kommaseparerad_lista_av_sekundär_diagnos_namn_med_diagnoskod_i_parentes>
Social historia: <kommaseparerad_lista_av_all_social_historia>
Tidigare medicinsk historia: <kommaseparerad_lista_av_alla_medicinska_tillstånd_före_inläggning>
Orsaker till inläggning: <kommaseparerad_lista_av_huvudorsak_till_inläggning>

Anteckning: ###
{note}
###

Visa resultatet i Markdown-format.