;; extends

; Przybliżenie semantic tokens z LSP: identyfikator pisany wielką literą przed kropką
; (np. WeaponCategory w WeaponCategory.Martial) traktuj jak typ.
; Działa też tam, gdzie nie ma klienta LSP (np. podgląd Telescope).
(member_access_expression
  expression: (identifier) @type
  (#lua-match? @type "^%u")
  (#set! priority 110))
