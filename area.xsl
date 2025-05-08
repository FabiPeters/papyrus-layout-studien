<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:math="http://www.w3.org/2005/xpath-functions/math" xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:p="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15" exclude-result-prefixes="#all" version="3.0">

    <xsl:output indent="yes"/>

    <xsl:variable name="coords">
        <xsl:variable name="coords_string" select="//p:TextRegion[@id = 'r2']/p:Coords/@points"/>
        <xsl:for-each select="tokenize($coords_string, ' ')">
            <point n="{position()}">
                <x>
                    <xsl:value-of select="tokenize(., ',')[1]"/>
                </x>
                <y>
                    <xsl:value-of select="tokenize(., ',')[2]"/>
                </y>
            </point>
        </xsl:for-each>
    </xsl:variable>
    
    <xsl:variable name="paragraph_area">
        <xsl:for-each select="$coords/point">
            <xsl:choose>
                <xsl:when test="position() != last()">
                    <xsl:variable name="x1" select="./x" as="xs:integer"/>
                    <xsl:variable name="y1" select="./y" as="xs:integer"/>
                    <xsl:variable name="x2" select="./following::x[1]" as="xs:integer"/>
                    <xsl:variable name="y2" select="./following::y[1]" as="xs:integer"/>
                    
                    <xsl:variable name="x1y2" select="$x1 * $y2"/>
                    <xsl:variable name="y1x2" select="$y1 * $x2"/>
                    
                    <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2" as="xs:integer"/>
                    
                    <value n="{position()}"><xsl:value-of select="$x1y2-y1x2"/></value>
                    
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="x1" select="./x" as="xs:integer"/>
                    <xsl:variable name="y1" select="./y" as="xs:integer"/>
                    <xsl:variable name="x2" select="/point[1]/x" as="xs:integer"/>
                    <xsl:variable name="y2" select="/point[1]/y" as="xs:integer"/>
                    
                    <xsl:variable name="x1y2" select="$x1 * $y2"/>
                    <xsl:variable name="y1x2" select="$y1 * $x2"/>
                    
                    <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2" as="xs:integer"/>
                    
                    <value n="{position()}"><xsl:value-of select="$x1y2-y1x2"/></value>
                    
                </xsl:otherwise>
            </xsl:choose>
            
            
        </xsl:for-each>
        
    </xsl:variable>
    
    <xsl:variable name="coords2">
        <xsl:variable name="coords_string2" select="//p:TextRegion[@id = 'r1']/p:Coords/@points"/>
        <xsl:for-each select="tokenize($coords_string2, ' ')">
            <point n="{position()}">
                <x>
                    <xsl:value-of select="tokenize(., ',')[1]"/>
                </x>
                <y>
                    <xsl:value-of select="tokenize(., ',')[2]"/>
                </y>
            </point>
        </xsl:for-each>
    </xsl:variable>
    
    <xsl:variable name="paragraph_area2">
        <xsl:for-each select="$coords2/point">
            <xsl:choose>
                <xsl:when test="position() != last()">
                    <xsl:variable name="x1" select="./x"/>
                    <xsl:variable name="y1" select="./y"/>
                    <xsl:variable name="x2" select="./following::x[1]"/>
                    <xsl:variable name="y2" select="./following::y[1]"/>
                    
                    <xsl:variable name="x1y2" select="$x1 * $y2"/>
                    <xsl:variable name="y1x2" select="$y1 * $x2"/>
                    
                    <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2"/>
                    
                    <value n="{position()}"><xsl:value-of select="$x1y2-y1x2"/></value>
                    
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="x1" select="./x"/>
                    <xsl:variable name="y1" select="./y"/>
                    <xsl:variable name="x2" select="/point[1]/x"/>
                    <xsl:variable name="y2" select="/point[1]/y"/>
                    
                    <xsl:variable name="x1y2" select="$x1 * $y2"/>
                    <xsl:variable name="y1x2" select="$y1 * $x2"/>
                    
                    <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2"/>
                    
                    <value n="{position()}"><xsl:value-of select="$x1y2-y1x2"/></value>
                    
                </xsl:otherwise>
            </xsl:choose>
            
            
        </xsl:for-each>
        
    </xsl:variable>
    
    <xsl:template match="/">
        <xsl:copy-of select="$paragraph_area"/>
        
        <xsl:variable name="sum" select="sum($paragraph_area/value)"/>
            
        <xsl:value-of select="$sum div 2"/>
        
        <xsl:copy-of select="$paragraph_area2"/>
        
        <xsl:variable name="sum2" select="sum($paragraph_area2/value)"/>
        
        <xsl:value-of select="$sum2 div 2"/>
        
        Prozentzahl: <xsl:value-of select="format-number($sum div $sum2 * 100, '###')"/>%
        
    </xsl:template>


</xsl:stylesheet>
