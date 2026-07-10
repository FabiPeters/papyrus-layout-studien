= Anhang
#linebreak()
== Abbildungen

#figure(
  image("P_09782-Pl-E_R_001.jpg"), caption: [Platte E von #cite(<BerlPap_9782>, form: "full").]
)

#page(flipped: true)[  
#figure(
  image("plate_A_layout_schema.svg", height: 85%), caption: [Schematische Darstellung des Layouts von Platte A.#footnote[Die Darstellung wurde von Claude Opus 4.8 erstellt und basiert auf den per Skript generierten Daten (https://github.com/FabiPeters/papyrus-layout-studien/blob/main/data/layout_data.json).]]
)
]

#include "tei_column_plate_map_anhang.typ"
#pagebreak()
#page(flipped: true)[ 

== Layoutdaten je Kolumne#footnote[Diese Tabelle wurde von Claude Opus 4.8 generiert und basiert auf den per Skript generierten Daten (https://github.com/FabiPeters/papyrus-layout-studien/blob/main/data/layout_per_column.csv).]
#include "layout_per_column.typ"

#pagebreak()
== Layoutdaten je Platte#footnote[Diese Tabelle wurde von Claude Opus 4.8 generiert und basiert auf den per Skript generierten Daten (https://github.com/FabiPeters/papyrus-layout-studien/blob/main/data/layout_summary_per_plate.csv).]
#include "layout_summary_per_plate.typ"
]

#pagebreak()
#include "ai_generated_content_declaration.typ"