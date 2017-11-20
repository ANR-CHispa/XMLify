#!/usr/bin/env python
# -*- coding: utf-8 -*-
#python 3 

#author : Nauge Michael & David Chesnet v1.1 (06/2017 - 10/07/2017)
'''
description : outil de conversion d'un fichier de métadonnées (CSV) en XML.
   Pour cela, on utilise un fichier de mapping qui fait correspondre à ch&que colonne de métadonnées
   une arborescence XML. cette "arborescence" est assemblée à un arbre vide, un fichier XML modèle.
   Chaque ligne de données est convertie en un fichier XML séparé dont le nom est construit à partir 
   de la donnée trouvée dans une colonne spécifiée par l'utilisateur.
'''

import csv                                 # lecture de fichier texte format CSV
import xml.etree.ElementTree as ET         # gestion d'un arbre XML
from random import randint                 # générateur de valeur aléatoire 
import copy                                # pour faire des copies "spéciales" comme copy.deepcopy 
import sys                                 # appel à des fonctions "système" (arguments ligne de commmande, par ex.)
import os                                  # gestion de fichier sur disque (effacement de fichier, par ex.)


# Constantes
msgFinDuJeu = '\n=> Processing stopped: please, correct.'


#--------------------------------------------------------------
def readError(filename):
    '''
    prints an error message when a file cannot be read.
    :param filename: name of the file
        :type: str
    '''
    print ('Failed to read file '+filename)
    
    return None


#--------------------------------------------------------------
def writeError(filename):
    '''
    prints an error message when a file cannot be written.
    :param filename: name of the file
        :type: str
    '''
    print ('Failed to create file '+filename)
    
    return None


#--------------------------------------------------------------
def indent(elem, level=0):
    '''
    in-place prettyprint formatter, from "http://effbot.org/zone/element-lib.htm#prettyprint"
    Prints a tree with each node indented according to its depth. 
    This is done by first indenting the tree (see below), and then serializing it as usual.
    indent: Adds whitespace to the tree, so that saving it as usual results in a prettyprinted tree.
    fonction récursive.

    :param elem: élément de l'arbre XML
        :type: xmltree element
    :param level: niveau d'indentation   
        :type: int    
    :returns: None    
    '''   
    
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            
    return None
                        
#--------------------------------------------------------------
def completeXMLheader(tmpfile, xmlBase):
    """
    créé un fichier XML en reprenant les déclarations dans le fichier XML "modèle", 
    puis y rajoute (recopie) le contenu du fichier temporaire contenant l'arborescence 
    XML fabriquée. A la fin, supprime le fichier temporaire.
    
    :param tmpfile: nom du fichier contenant l'arbre XML généré
        :type : string
    :param XmlBase: fichier contenant l'arbre XML de base   
        :type: str   
    :returns: None
    """
    
    xmlTag =''  # balise pivot qui sert à repérer la fin des déclarations et le début de l'arbre XML
    # ouvrir en écriture tmpfile+'.xml'
    try:
        with open(tmpfile+".xml", "w",encoding="utf-8") as result_file:            
            try:
                # ouvrir en lecture 'teiHeader.xml'
                header_file = open(xmlBase, "r",encoding="utf-8")    
                # lire chaque ligne jusqu'à tomber sur une balise type '<tei>'
                declStart = False
                declStop = False
                for ligne in header_file:     
                    if (ligne==''):
                        break
                    # supprimer les ' ', '\n', etc... 
                    ligne = ligne.strip()  
                    # a-t-on une balise de début de déclaration ou de commentaire ?
                    if (declStart == False):
                        declStart = (ligne.find('<!')>-1)or(ligne.find('<?')>-1)
                    # a-t-on une balise de fin de déclaration ou de commentaire ?
                    if (declStop == False):    
                        declStop = ((ligne.find('-->')>-1)or(ligne.find('?>')>-1))
                        
                    # ni déclaration, ni commentaire et pas vide: c'est qu'on attaque l'arbre XML
                    if (declStart == False) and (declStop == False) and (not(ligne == '')):
                        # On a trouvé notre balise "pivot": on prend '<' et deux autres caractères
                        xmlTag = ligne[:3]
                        break   # on ne cherche plus, ce n'est pas la peine                
                    # écrire cette ligne dans tmpfile+'.xml' à condition qu'elle ne soit pas vide
                    if not(ligne==''):
                        result_file.write(ligne+'\n')  # on remet une fin de ligne car strip() l'a supprimé
                        # si on a copié une déclaration/commentaire complet, on remet les compteurs à zéro
                        if (declStart == True) and (declStop == True):
                            declStart = False
                            declStop = False
            except EnvironmentError:
                readError(xmlBase)
            finally:
                # fermer 'teiHeader.xml'
                header_file.close()
                ligne=''       
            try:
                # ouvrir en lecture tmpfile+'.tmp'
                tree_file = open(tmpfile+".tmp", "r",encoding="utf-8")
                # recopier chaque ligne de l'arbre dans tmpfile+'.xml'
                debut = 0
                for ligne in tree_file:
                    if (ligne == ''):
                        break
                    if (ligne.find(xmlTag)>-1):
                        debut = 1
                    if debut == 1:
                        result_file.write(ligne)
            except EnvironmentError :
                readError(tmpfile+".tmp")
            finally:
                # fermer tmpfile+'.tmp'
                tree_file.close()                
                os.remove(tmpfile+'.tmp')
    except EnvironmentError:
        writeError(tmpfile+".xml")
    return None
           
#--------------------------------------------------------------
def loadCSVtoTEIMapping(pathFileCSV_Map):
    """
     Charge le fichier CSV de mapping entre les champs personnalisés et les champs TEI 
     
     :param pathFileCSV_Mapp : le chemin vers le fichier csv contenant le mapping entre des champs de metas personnalisées et des champs normalisés contenus dans un header TEI
         :type str
    : returns: row
        :type: orderedDict  
    """
    
    Dico = None
    try:
        with open(pathFileCSV_Map,encoding='utf-8') as csvfileMap:
            readerMap = csv.DictReader(csvfileMap, delimiter=';')
             #on obtien un dico par ligne
            for row in readerMap:
                Dico = row
                break
        # exemple: clef row['Creator'] renvoie '<teiHeader><fileDesc><titleStmt><author key=""></autor></fileDesc></titleStmt></teiHeader>'
    except EnvironmentError:
        readError(pathFileCSV_Map)
        
    finally:
        csvfileMap.close()
    # on renvoie la dernière ligne
    return Dico
    
#--------------------------------------------------------------    
def check_TEIMapping(TEIMapping, declarations):
    """
    Vérifie le mapping TEI: pas de clef ou de valeur vide. Au passage, supprime les clefs avec valeur "none".
    
    :param TEIMapping : dictionnaire ordonné contenant les couples "entête de colonne"->"balises"
        :type orderedDict
    :param decalarations: liste des balises de déclaration d'espaces de nommage (namespace, i.e. 'xmlns:')
        :type list
    : returns: ckecked_Ok: la vérification s'est bien passée ou il y a des choses à corriger
        :type bool
    """
    
    ckecked_Ok = True
    # liste des clefs à supprimer du dictionnaire
    KeystoDelete = []
    n = 0
    for clef in TEIMapping:
        n = n+1
        nkey = str(clef).strip()
        # on vérifie que la clef est correcte
        if (clef is None) or (nkey == ''):            
            print('Warning: column ',n,'is empty\n')
            # erreur à corriger: on arrêtera le traitement
            ckecked_Ok = False
        else:   # la clef est correcte
            # on récupère les balises TEI correspondantes
            value = TEIMapping.get(clef,None)
            nvalue = str(value).strip().lower()
            # on vérifie que la valeur existe
            if (value is None) or (nvalue == ''):
                print('Warning: column ',n,' ',clef,'= "No mapping string"\n')
                # erreur à corriger: on arrêtera le traitement
                ckecked_Ok = False
            else:    # on a une valeur de conversion 
                # si on a décidé de ne pas convertir ce champs    
                if (nvalue == 'none'):
                    # on ajoute la clef à la liste des clefs à supprimer du dictionnaire
                    KeystoDelete.append(clef)
                else:    
                    # Si on a un mapping qui n'est pas sous forme de balises, le tranformer en balises
                    if (nvalue.find('<')==-1):
                        tmpStr = '<'+nvalue+'>?</'+nvalue+'>'
                        TEIMapping[clef] = tmpStr
                    '''
                    Si on a un (des) espace(s) de nommage, on doit encadrer les balises avec, sinon
                    le parsing en arbre ne pourra se faire, car le parser ne pourra pas interpréter
                    les noms de balises qualifiés (ex: "dcterms:description").
                    insérer de l'intérieur vers l'extérieur les déclarations "namespace" et les balise de fin: 
                    d'abord <decl2><mapping></decl2>, puis <decl1><decl2><mapping></decl2></decl1>        
                    '''
                    if (len(declarations)>0):
                        for nDecl in reversed(declarations):
                            myList = nDecl.split(' ')  # récupérer '<nlk:Data' par ex.
                            tmpStr = nDecl + TEIMapping[clef] + '</'+myList[0][1:]+'>'
                            # on modifie la valeur dans le dictionnaire de mapping, pour de vrai !
                            TEIMapping[clef] = tmpStr 
                            value = TEIMapping.get(clef,None)
                    try:                
                        ET.fromstring(value)                                        
                    except ET.ParseError as e:
                        print('\nError in XML string on field n°'+str(n)+': "'+clef+'" <-> "'+value+'"')
                        print ('->',e.msg)
                        ckecked_Ok = False

    if (ckecked_Ok == True) and  (len(KeystoDelete) > 0) :
        for idx in KeystoDelete:
            # supprimer chaque clef inutile du dictionnaire de mapping
            del(TEIMapping[idx])
    
    return ckecked_Ok


#--------------------------------------------------------------
def cleanXMLFromEmptyLeaf(TEItree):
    '''
    Supprime les feuilles vides de l'arbre XML, sous la racine uniquement (1er niveau d'arborescence)
    Les éléments ayant une descendance, ne sont pas des feuilles, mais des branches...
    :param TEItree: arbre XML à traiter
        :type: ElementTree
    :returns: None        
    '''
    toDelete = []
    rootNode = ET.ElementTree.getroot(TEItree)    # insertionPoint est un Element
    for node in rootNode:
        # pas de texte
        if ((node.text==None) or (node.text=='')):
            # pas de descendant
            if (len(list(node))==0):
                # on met dans une liste de noeuds à supprimer
                toDelete.append(node)            
    for node in toDelete:
        rootNode.remove(node)
        
    return None


#--------------------------------------------------------------
def AddToTree(TEItree,belleclef):
    """
     Ajoute les balises TEI mappées à l'arbre XML 
     "belleclef" (mini-arborescence sous forme de texte) est convertie en arbre XML. 
     On ajoute cet arbre à l'arbre principal(TEItree), au moins ce qu'il a et qui n'est
     pas dans l'arbre principal.
     
    :param TEItree : arbre 
        :type ElementTree
    :param belleclef : chaine de balises TEI contenant les données d'un champ
        :type string
    :returns: None
    """
    
    # on commence la recherche à la racine de l'arbre XML
    insertionPoint = ET.ElementTree.getroot(TEItree)    # insertionPoint est un Element
    # ET.dump(TEItree)    
    oldInsertionPoint = insertionPoint
    # on créé un petit arbre XML avec la chaine de "mapping"
    miniTree = ET.fromstring(belleclef)
        
    # parcourir le mini arbre du haut vers le bas 
    for balise in miniTree.iter():
        found = False
        '''
        Si la racine est la même pour les deux arbres, ça pose problème puisqu'on va commencer 
        à chercher la balise "racine" du miniTree sous la racine de TEItree. Il faut donc passer son tour...
        '''
        if (balise.tag == insertionPoint.tag):
            pass
        else:    
            for candidat in insertionPoint.findall(balise.tag):           
                # si on a trouvé la même balise avec le même attribut (attribut est du type "dict")          
                if (candidat is not None) and (candidat.attrib == balise.attrib) and (found==False):
                    ''' 
                    on retraite les champs "texte" de la balise et de la balise courante de l'arbre (dans des variables
                    temporaires) pour qu'elle contienne du texte (type str) nettoyé des espaces, retour chariot et autres 
                    caractères indésirables que l'on peut trouver avant et après le texte. Le champ texte peut être de 
                    type None et pas str (chaine vide).
                    '''
                    if candidat.text==None:
                        contenuC = ''
                    else:
                        contenuC=candidat.text    
                    if balise.text==None:
                        contenuB = ''
                    else:
                        contenuB=balise.text
                    contenuC=contenuC.strip()
                    contenuB=contenuB.strip()
                    found = True
               
                    oldInsertionPoint = insertionPoint
                    insertionPoint = candidat
                    # s'il n'y a pas de contenu dans la balise "courante" de l'arbre ("candidat")    
                    if (contenuC==''):   
                        # et on a un nouveau texte
                        if not(contenuC==contenuB):  
                            # alors, on insere le texte dans la balise de l'arbre
                            insertionPoint.text=balise.text                                                         
                    else:        # on a du texte dans "candidat"
                        # on a aussi du contenu (différente) dans la balise, au même niveau    
                        if (not(contenuC==contenuB)) and (not(contenuB=='')):   
                            # On va forcer la répétition de la balise au même niveau, mais avec un autre texte
                            # on recherche le "numéro" de noeud du dernier "Candidat"
                            idx = 0
                            gotIt = False
                            for node in oldInsertionPoint:
                                if not(node.tag == candidat.tag):
                                     # rechercher le 1er "candidat" dans les nodes
                                    if gotIt ==False:
                                        idx = idx + 1                                    
                                    else:   # on a dépassé la liste des noeuds correspondants à la recherche
                                        break  # on arrête la recherche, car on atrouvé l'emplacement d'insertion
                                
                                else:   # on a trouvé le 1er noeud correspondant à la recherche
                                    if gotIt==False:
                                        gotIt = True
                                    # compter les candidats
                                    idx = idx + 1
                            # element.insert(index,element): inserts subelement at the given position in this element.
                            oldInsertionPoint.insert(idx,balise)
                            insertionPoint = oldInsertionPoint
            # la balise n'est trouvée dans l'arbre
            if (found == False):    
                # on insère la balise après le point courant dans l'arbre
                insertionPoint.append(balise)
                # le nouveau point d'insertion est la balise que l'on vient d'insérer
                insertionPoint = balise
                found = True
                  
    return None

#--------------------------------------------------------------
def dispatchValues(clef, valeurs):
    """
    Ventile les morceaux de texte séparés par '|' (contenus dans "valeurs") à la place des '?' 
    dans les balises (contenues dans "clef"), terme à terme. S'il y a plus de valeurs que de points d'insertion,
    les dernières valeurs sont concaténées dans le dernier point d'insertion.
    
    :param clef: balises XML
        :type string
    :param valeurs: contenu du champ "texte"
        :type string
    : returns: clef 
        :type string
    """
    
    listeValeurs = str(valeurs).split('|') 
    nbValeurs = len(listeValeurs)
    nbInterrogations = clef.count('?')    
    cpt = 0
    while cpt < nbInterrogations:
        if cpt < nbValeurs:
            if ( ((cpt+1)==nbInterrogations) and (nbValeurs > nbInterrogations) ):
                 # remplacer le dernier élément par le reste, s'il y a plus de valeurs que de points d'interrogation 
                 chaine = ('|').join(listeValeurs[cpt:])
            else:    
                chaine =listeValeurs[cpt]
            # un seul remplacement d'un seul '?' à la fois    
            clef = str(clef).replace('?',chaine,1)
        cpt = cpt + 1 
        
    return clef

#--------------------------------------------------------------
def doMap_aRow(XMLTree, row, numRow, TEIMapping, nameColumn, outPath, verbose, cleanEmptyLeaf):
    """
    Applique le mapping TEI sur une ligne de données.
    
    :param XMLTree: arbre XML de base
        :type xml.elementree
    :param row : dictionnaire ordonné contenant les couples "entête de colonne"->"données"
        :type orderedDict
    :param numRow: numéro de la ligne
        :type int        
    :param TEIMapping : dictionnaire ordonné contenant les couples "entête de colonne"->"balises TEI"
        :type orderedDict
    :param nameColumn: nom de la colonne dont la donnée sert à fabriquer le nom du fichier XML créé
        : type: str
    :param outPath: dossier pour stocker le fichiers créés
        :type: str    
    :returns: chemin d'accès (outPath+cote)
        :type: str
    """

    # on démarre avec un bel arbre tout propre, une copie de l'abre XML "minimal" de base
    TEItree = copy.deepcopy(XMLTree)
    cote = ''
    # on traite chaque ligne, colonne par colonne 
    for colonne in row:
        # pour chaque entête de colonne, récupérer la cellule contenant la valeur
        valeur = row.get(colonne,None)
        # on ne recherche que pour des champs ayant une valeur
        if not(((valeur).strip()).lower() == 'none'):
            if colonne == nameColumn:
                cote = valeur
            # chercher les balises TEI correspondant à l'entête de colonne dans TEIMapping
            newclef = TEIMapping.get(colonne,None)
            # si on trouve la correspondance
            if not(newclef is None):              
                # remplacer les "?" par les morceaux de valeur
                belleclef = dispatchValues(newclef, valeur)
                # ajouter à l'arbre XML
                AddToTree(TEItree,belleclef)  
            else:
                if verbose:
                    print('Line',str(numRow),'-> no mapping for "',colonne,'"') 
    
    # nettoyage des feuilles vides de l'arbre
    if cleanEmptyLeaf==True:
        cleanXMLFromEmptyLeaf(TEItree)
        
    # mise en forme de l'arbre
    indent(ET.ElementTree.getroot(TEItree))            
    # exporter le fichier XML
    if cote == '':
         # au cas où on n'aurait pas de nom pour le fichier à écrire
        cote = 'line_'+str(numRow)+'_' + str(randint(0,65535))
        # lever un warning, donner le numéro de ligne et le nom de fichier 
        print('!!! No filename found for line '+str(numRow)+'. Outpu file will be named: '+cote+'.xml')    
    # création d'un fichier temporaire (sera complété par la suite)    
    try:    
        TEItree.write(outPath+cote+'.tmp', encoding="UTF-8")
    except EnvironmentError:
        writeError(outPath+cote+'.tmp')
        return None
    
    # renvoie le chemin d'accès du fichier, sans extension
    return outPath+cote
       
#--------------------------------------------------------------
def processCSVSource(XMLTree, XmlBase, TEIMapping, pathFileCSV_Source, nameColumn, outPath, verbose, cleanEmptyLeaf):
    """
    Charge le fichier CSV contenant les champs personnalisés et le converti en série de balises XML.
    Créé un fichier XML par ligne de données. La règle de conversion est dans le dico "TEImapping".
    
    :param XMLTree: arbre XML de base
        :type xml.elementree
    :param XmlBase: fichier contenant l'arbre XML de base   
        :type: str
    :param TEIMapping: dictonnaire contenant le mapping métadonnée -> balises XML
    :param pathFileCSV_toMap: le chemin vers le fichier csv contenant la table des données
         :type: str  
    :param nameColumn: nom de la colonne dont la donnée sert à fabriquer le nom du fichier XML créé
        :type: str     
    :param outPath: dossier pour stocker le fichiers créés
        :type: str
    : returns: none
    """
    
    try:
        with open(pathFileCSV_Source, encoding='utf-8') as csvfileSource:
            readerSource = csv.DictReader(csvfileSource, delimiter=';') 
             # on boucle sur chaque ligne du dico source
            numRow = 1    # la ligne 0 n'est pas comptée car c'est la ligne d'entêtes de colonnes 
            for row in readerSource:
                numRow = numRow + 1
                # traite la ligne et créé un fichier temporaire (fName)
                fName = doMap_aRow(XMLTree, row, numRow, TEIMapping, nameColumn, outPath, verbose, cleanEmptyLeaf)
                              
                if not(fName==None):
                    '''
                    Compléter le fichier fName avec les déclarations XML du fichier XML de base qui ont
                    été supprimées lors du parsing (XMLTree gère très mal les déclarations XML). 
                    '''
                    completeXMLheader(fName, XmlBase)  
    except EnvironmentError:
        readError(pathFileCSV_Source)
        print(msgFinDuJeu)
    finally:
        csvfileSource.close()     
        
    return None

#--------------------------------------------------------------    
def retrieveNamespaces(XmlBase, namespaces, declarations):
    """
    Récupérer les déclarations d'espace(s) de nommage, s'il y en a, dans deux structures,
    un dictionnaire qui les contient sous la forme "tag:URI" et une liste contenant les balises
    complètes.
       
    :param XmlBase: nom du fichier XML "minimal" de base
        :type str
    :param namespaces : dictionnaire contenant les couples "TAG":"URI"
        :type dict
    :param declarations: liste des balises de déclarations (forme <...xmslns:...>)
        :type list        
    :returns: l'opération a réussi ou non
        :type: boolean  
    """
    
    nsTag = 'xmlns:'  # mot-clef déclarant un espace de nommage dans une balise
    TmpDecl = ''      # str temporaire pour accumuler les morceaux de balise
    try:
        nsStart = False
        nsStop = False
        with open(XmlBase,encoding='utf-8') as xmlfileTemp:
           for ligne in xmlfileTemp:     
                if (ligne==''):
                    break
                # supprimer les ' ', '\n', etc... 
                ligne = ligne.strip()  
                # a-t-on une ligne à traiter ?
                if not(ligne == ''):
                    #mettre la déclaration des namespaces en dico
                    if (ligne.find(nsTag) >-1):
                        # éclater la ligne en tableau de chaines et récupérer ce que l'on veut
                        # print('\n',ligne,'\n')
                        mytab = ligne.split(' ')
                        # print(mytab)                        
                        for entree in mytab:
                            #print('\n',entree,'\n')
                            StartPos = entree.find(nsTag)
                            if (StartPos>-1)and(entree.find(':xsi=')==-1):
                                tmpStr =entree[StartPos+len(nsTag):]  # ex: nkl="http://nakala.fr/schema#" 
                                prefix = tmpStr[:tmpStr.find('=')]
                                uri = tmpStr[tmpStr.find('"')+1:-1]
                                # print('\n',prefix,'||',uri,'\n')
                                namespaces[prefix] = uri      
                
                    # reconstituer la "balise" de déclaration complète et la stocker dans "declarations"
                    # (la balise peut être répartie en plusieurs lignes)
                    if (nsStart == False):
                        TmpDecl = ''
                        nsStart = (ligne.find(nsTag)>-1)and(ligne[0]=='<')
                        nsStop = (ligne[-1]=='>')
                        # on a une déclaration en une seul ligne
                        if nsStart:
                            TmpDecl = ligne
                        if nsStop:
                            nsStart = False
                            nsStop = False
                    else:
                        if (nsStop == False):
                            TmpDecl = TmpDecl +' '+ligne
                            if (ligne[-1]=='>'):
                                nsStart = False
                                nsStop = False 
                                declarations.append(TmpDecl)                                  
        if (len(namespaces)>0):
            for prefix, uri in namespaces.items():
                # The .register_namespace() function is only useful for when serializing a tree out to text again.
                ET.register_namespace(prefix, uri)   # ex: ET.register_namespace('nkl','http://nakala.fr/schema#')
    except EnvironmentError:
        readError(XmlBase)
        return False 
    
    return True

#--------------------------------------------------------------    
def convertCSVToXML(XmlBase, CSV_mapFile, CSV_dataFile, nameColumn, outPath, verbose = False, cleanEmptyLeaf = True):
    """
    Converti un fichier de données CSV en une série de fichiers XML
    
    :param XmlBase: fichier contenant l'arbre XML de base   
        :type: str
    :param CSV_mapFile: chemin du fichier CSV de mapping métadonnées - balises XML
        : type: str
    :param CSV_dataFile: chemin du fichier CSV de métadonnées
        : type: str
    :param nameColumn: nom de la colonne dont la donnée sert à fabriquer le nom du fichier XML créé
        : type: str
    :param outPath: dossier de destination des fichiers XML
        : type: str
    : returns: none
    """
       
    namespaces = {}   # dictionnaire pour stocker les paires prefix, uri
    declarations =[]  # liste contenant la reconstitution des balises de déclaration des namespaces
    
    if (retrieveNamespaces(XmlBase,namespaces,declarations) == False):
        return None    
    try:
         # charger l'arbre de base ("minimal") XML
        XMLTree = ET.parse(XmlBase)
    except ET.ParseError as e:
        linenum, colnum = e.position
        print('File '+XmlBase+' has a mistake (line '+str(linenum)+';column '+str(colnum)+')')
        print ('->',e.msg)
        print(msgFinDuJeu)
    else:   
        # charger le fichier de mapping dans un dico
        TEIMapping = loadCSVtoTEIMapping(CSV_mapFile)
        # si il est valide, on procède aux conversions    
        if (not(TEIMapping==None)) and (check_TEIMapping(TEIMapping, declarations) == True):
            processCSVSource(XMLTree, XmlBase, TEIMapping, CSV_dataFile, nameColumn, outPath, verbose, cleanEmptyLeaf)    
        else:
            print(msgFinDuJeu)
            
    return None    


#--------------------------------------------------------------
def is_valid_directory(parser, arg):
    """
    Check if arg is a valid directory that already exists on the file system.

    :param parser : argparse object
        type: ??
    :param arg: directory path name
        type: str
    :Returns:
        type: str
    """
    if not os.path.isdir(arg):
        parser.error("The folder %s does not exist!" % arg)
    else:
        return arg

#--------------------------------------------------------------
def is_valid_file(parser, arg):
    """
    Check if arg is a valid file that already exists on the file system.
    
    :param parser : argparse object
        type: ??
    :param arg: file path name
        type: str
    :Returns:
        type: str
    """
    if not os.path.isfile(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg
    return None

#--------------------------------------------------------------
# les tests
#--------------------------------------------------------------
def convertCSVToXML_test(isTEI):
    # Variables  pour le test
    if isTEI:
        pathFileCSV_Map = './input/mapping.csv'  
        pathFileCSV_Source = './input/datasample.csv'  # testmapping
        resultPath = './output/'
        refColonne = 'Cote'   # entête de la colonne servant à créer le nom du fichier XML résultat
        XmlBaseFile = 'teiHeader.xml'
        verbose = True
        cleanEmptyLeaf = True
    else:
        pathFileCSV_Map = './input/mappingShortNklify.csv'  
        pathFileCSV_Source = './input/GuarnidoShortNklReady.csv'  # './input/GuarnidoShortNklReady.csv' # GuarnidoNkl
        resultPath = './output/'
        refColonne = 'Source'  
        XmlBaseFile = 'NakalaHeader.xml' 
        verbose = False
        cleanEmptyLeaf = True
    convertCSVToXML(XmlBaseFile ,pathFileCSV_Map, pathFileCSV_Source, refColonne, resultPath, verbose, cleanEmptyLeaf)    
    
    return None

#--------------------------------------------------------------
#--------------------------------------------------------------    

if __name__ == '__main__':
    
    import argparse                            # pour traiter les arguments en ligne de commande
    parser = argparse.ArgumentParser()
    parser.add_argument("XmlBase", type=lambda x: is_valid_file(parser, x), help='minimum XML tree file. Set path and name. ex: "./input/teiHeader.xml".')
    parser.add_argument("mapFile", type=lambda x: is_valid_file(parser, x),help='CSV text file containing column headers and mapping to XML tags. Set file path and name. ex: "./input/mapping.csv".')
    parser.add_argument("dataFile", type=lambda x: is_valid_file(parser, x),help='CSV text file containing column headers and data. Set file path and name. ex: "./input/datasample.csv".')
    parser.add_argument("outFolder", type=lambda x: is_valid_directory(parser, x),help='set folder path to store resulting XML files. Ex: "./output/".')
    parser.add_argument("refColumn", help='header of column containing unique value that will be used to forge resulting XML file name. Ex: "cote".')
                        
    parser.add_argument("-v", "--verbose", help="option verbose: set this option to be informed of data column not mapped to XML. Default is False.", action="store_true")
    parser.add_argument("-n", "--noclean", help="set this option if you do not want empty XML tag be remove from the XML tree. Default is True.", action="store_false")
    
    # si on a au moins un paramètre en ligne de commande
    if len(sys.argv)>1:   
        args = parser.parse_args()
        convertCSVToXML(args.XmlBase ,args.mapFile, args.dataFile, args.refColumn, args.outFolder, args.verbose, args.noclean)
    else:
        parser.print_help()
       
           
    # convertCSVToXML_test(False)  # Nakala 
    # convertCSVToXML_test(True)   # TEI