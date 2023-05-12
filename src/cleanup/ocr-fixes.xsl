<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
  xmlns:map="http://www.w3.org/2005/xpath-functions/map"
  xmlns:local="local"
  exclude-result-prefixes="xs xd"
  expand-text="true"
  version="3.0">
  <xd:doc scope="stylesheet">
    <xd:desc>
      <xd:p><xd:b>Created on:</xd:b> May 12, 2023</xd:p>
      <xd:p><xd:b>Author:</xd:b> pd</xd:p>
      <xd:p>Helper script to correct some OCR mistakes.</xd:p>
      <xd:p>Run from command-line after installing Saxon: 
        <xd:pre>java -jar /opt/Saxonica/SaxonHE12-2/saxon-he-12.2.jar -s:ocr-fixes.xsl -xsl:ocr-fixes.xsl input=bern-addresses/proofread/1903-11-02.txt</xd:pre>
      </xd:p>
    </xd:desc>
  </xd:doc>
  
  <xsl:output method="text" indent="true"/>
  
  <xsl:param name="input" as="xs:string" select="'../../proofread/1900-02-15.txt'"/>

  <xsl:variable name="ocr-fixes" as="map(xs:string, xs:string)" select="map {
        '(.)g\sasse'  : '$1gasse',
        'Aarberger5 asse' : 'Aarbergergasse',
        'Amt-\sj?haus'  : 'Amthaus',
        'Biichler'    : 'Büchler',
        'Bierkiller'  : 'Bierkeller',
        'Biirgi'      : 'Bürgi',
        'Biichi'      : 'Büchi',
        'Bliimli'     : 'Blümli',
        '(B|b)riick'      : '$1rück',
        '(b|B)(l|i)ihl'  : '$1ühl',
        'bevg'        : 'berg',
        'Ghokolade'   : 'Chokolade',
        'Cliristoffel': 'Christoffel',
        'Civiistandsamt'  : 'Civilstandsamt',
        'Etfinger'    : 'Effinger',
        'Erlacnstr'   : 'Erlachstr',
        'e?n\sweg'     : 'enweg',
        'Froliberg'   : 'Frohberg',
        'fiihrer'     : 'führer',
        'Fiirspr'     : 'Fürspr',
        'gasse(\d+)'  : 'gasse $1',  
        '(g|G)ehiilf' : '$1ehülf',
        'grabeii'     : 'graben',
        'llelvetia|Ilelvetia'   : 'Helvetia',
        'hiibeli|lnibeli' : 'hübeli',
        'Hiinerwadel' : 'Hünerwadel',
        'höfii'       : 'höfli',
        'fjheweg'     : 'Höheweg',
        'Hötel'       : 'Hôtel',
        'Iiirschen|Hirsclien' : 'Hirschen',
        'Hirschenf\sraben'  : 'Hirschengraben',
        'jiiger'      : 'jäger',
        'Tunkerngasse|Junkern-\s1gasse'  : 'Junkerngasse',
        'Turastrasse' : 'Jurastrasse',
        'Kädereckemvcg' : 'Kädereckenweg',
        'Kirclienfeld|Kirchen-\sIfeld': 'Kirchenfeld',
        'Liithi'      : 'Lüthi',
        'meclianik'   : 'mechanik',
        'Aletzgerg'   : 'Metzgerg',
        'Mmeral'      : 'Mineral',
        'miihle'      : 'mühle',
        'Miinz'       : 'Münz',
        'AIusik'      : 'Musik',
        'numiner'     : 'nummer',
        'Pappehveg'   : 'Pappelweg',
        'Reicnen'     : 'Reichen',
        'scnaft'      : 'schaft',
        'Schanzen-\s\{strasse' : 'Schanzenstrasse',
        'Schitflaube' : 'Schifflaube',
        'Scnosshalde' : 'Schosshalde',
        'Schiirch'    : 'Schürch',
        'sclnveizer'  : 'schweizer',
        'Sclnvarz|Scliwarz' : 'Schwarz',
        'Seidenvreg'  : 'Seidenweg',
        'Stand weg'   : 'Standweg',
        'strasse(\d+)'  : 'strasse $1',
        'Teie-S\sraphen':  'Telegraphen',
        'Yerlag'      : 'Verlag',
        'vveg'        : 'weg',
        'AVegmiiller' : 'Wegmüller',
        'Wiith'       : 'Wüth',
        '\\Vildhain'   : 'Wildhain',
        'Wlttikofen'  : 'Wittikofen',
        'W\syler'     : 'Wyler'
        }"/>
  
  <xsl:variable name="lines" select="unparsed-text-lines($input)"/>
  
  <xsl:template match="/">
    <xsl:for-each select="$lines">
      <xsl:sequence select="fold-left(map:keys($ocr-fixes), ., function($str, $regex) { replace($str,
        $regex, map:get($ocr-fixes,$regex)) } )"/><xsl:text>
</xsl:text>
    </xsl:for-each>
  </xsl:template>
  
</xsl:stylesheet>