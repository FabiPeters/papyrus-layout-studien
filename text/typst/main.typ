

#set document(title: [Title], author: "Author")
#set heading(numbering: "1.")
#set par(justify: true, first-line-indent: 1em, leading: 1em)
#set text(
  lang: "de"
)
#set page(margin: 3cm)

#include "title.typ"

#include "toc.typ"

#set page(numbering: "1", number-align: right)
#counter(page).update(1)

#include "text.typ"

#set heading(numbering: none)
#pagebreak()
#include "bibliography.typ"
#pagebreak()
#include "appendix.typ"

