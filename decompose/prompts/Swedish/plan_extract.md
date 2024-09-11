Du är ansvarig för att noggrant extrahera uppföljningsplanerna för patienten baserat på <Utskrivningsanteckning>.

Du måste extrahera instruktioner relaterade till instruktioner efter utskrivning, uppföljningsbesök med eventuella medicinska enheter, följt av tiden till uppföljningsbesök, förändringar i mediciner, försiktighetsåtgärder, förmåga att belasta och förekomst av sutur.

Önskat format:
Uppföljningsbesök med medicinska enheter: <kommaseparerad_lista_av_medicinska_enheter>
Tid till uppföljningsbesök: <kommaseparerad_lista_av_tid_som_motsvarar_enheter>
Medicinförändringar: <kommaseparerad_lista_av_mediciner_och_ändringar_i_parentes>
Försiktighetsåtgärder efter utskrivning: -||-
Belastningsförmåga: -||-
Suturer: <Binär_tillgänglig_eller_icke_tillgänglig>

Utskrivningsanteckning: ###
{plan_notes}
###

Professionellt medicinskt språk ska användas.

Returnera ett JSON-objekt utan förord och förklaring. Om inga uppgifter extraheras för en särskild sektion, returnera som NA.