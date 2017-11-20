# XMLify
Outil de conversion d'un fichier de métadonnées (CSV) en XML. Pour cela, on utilise un fichier de mapping qui fait correspondre à chaque colonne de métadonnées une arborescence XML. Cette "arborescence" est assemblée à un arbre vide : un fichier XML modèle. Chaque ligne de données est convertie en un fichier XML séparé, dont le nom est construit à partir de la donnée trouvée dans une colonne spécifiée par l'utilisateur.

Actuellement le lancement s'effectue en ligne de commande en vue d'une utilisation "massive" automatisée dans une chaine de traite
ment complète. Nous pensons développer une interface graphique facilitant sa prise en main. 

Pour lancer ce programme en ligne de commande :
>> python XMLify.py XmlBase mapFile dataFile outFolder refColumn 

-XmlBase : un fichier XML-TEI minimal contenant un arbre XML-TEI vide mais valide. Par défault utilisez le fichier teiHeader.xml
-mapFile : un fichier CSV contenant les règles de conversions entre les données brut (csv) et son équivalence en TEI. Par défault utilisez le fichier mapping.xml
-dataFile : fichier CSV contenant les données bruts à encoder. Pour un essai utilisez le fichier datasample.csv
-outFolder : le dossier de destination pour les fichiers XML-TEI générés par ce programme 
-refColumn : un nom de colonne present dans le dataFile utilisé pour produire des noms de fichiers de sorties distincts et intelligibles. Par exemple la "cote".

