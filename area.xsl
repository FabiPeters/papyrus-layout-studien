<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:math="http://www.w3.org/2005/xpath-functions/math" xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:p="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15" exclude-result-prefixes="#all" version="3.0">

    <xsl:output indent="yes"/>

    <xsl:variable name="imageWidth" select="//p:Page/@imageWidth"/>
    <xsl:variable name="imageHeight" select="//p:Page/@imageHeight"/>

    <xsl:variable name="fragment">
        <xsl:variable name="points_string" select="//p:TextRegion[contains(@custom, 'page')]/p:Coords/@points"/>
        <xsl:call-template name="get_values">
            <xsl:with-param name="points_string" select="$points_string"/>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="paragraphs">
        <xsl:for-each select="//p:TextRegion[contains(@custom, 'paragraph')]">
            <xsl:variable name="points_string" select="./p:Coords/@points"/>
            <paragraph n="{position()}">
                <xsl:call-template name="get_values">
                    <xsl:with-param name="points_string" select="$points_string"/>
                </xsl:call-template>
            </paragraph>
        </xsl:for-each>
    </xsl:variable>

    <xsl:template match="/">
        <xsl:copy-of select="$paragraphs"/>
        <xsl:copy-of select="$fragment"/>
        <empty_space>
            <xsl:value-of select="format-number((1 - sum($paragraphs//area) div $fragment/area), '##.#%')"/>
        </empty_space>

        <xsl:result-document href="page.svg">
            <svg xmlns="http://www.w3.org/2000/svg" width="{$imageWidth div 10}" height="{$imageHeight div 10}">
                <!-- Fragment outline (main papyrus boundary) -->
                <polygon points="{string-join($fragment//point/concat(x div 10, ',', y div 10), ' ')}" 
                         fill="none" 
                         stroke="red" 
                         stroke-width="1"
                         opacity="1"/>
                
                <!-- Paragraph regions -->
                <xsl:for-each select="$paragraphs/paragraph">
                    <polygon points="{string-join(.//point/concat(x div 10, ',', y div 10), ' ')}" 
                             fill="rgba(100, 150, 200, 0.3)" 
                             stroke="rgb(50, 100, 150)" 
                             stroke-width="0.2"/>
                    
                    <!-- Add paragraph number and area label at centroid -->
                    <xsl:variable name="centroid_x" select="sum(.//point/x) div count(.//point) div 10"/>
                    <xsl:variable name="centroid_y" select="sum(.//point/y) div count(.//point) div 10"/>
                    <text x="{$centroid_x}" y="{$centroid_y}" 
                          text-anchor="middle" 
                          dominant-baseline="central"
                          font-family="Arial, sans-serif" 
                          font-size="20" 
                          fill="rgb(50, 100, 150)"
                          font-weight="bold">
                        <xsl:value-of select="@n"/>
                    </text>
                    <!-- Add area value below the number -->
                    <text x="{$centroid_x}" y="{$centroid_y + 20}" 
                          text-anchor="middle" 
                          dominant-baseline="central"
                          font-family="Arial, sans-serif" 
                          font-size="12" 
                          fill="rgb(50, 100, 150)">
                        <xsl:value-of select="format-number(area, '#,###')"/> px²
                    </text>
                </xsl:for-each>
                
                <!-- Fragment area display in lower left -->
                <g transform="translate(20, {$imageHeight div 10 - 40})">
                    <rect x="0" y="0" width="150" height="30" fill="white" stroke="red" stroke-width="1" opacity="0.9"/>
                    <text x="10" y="15" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="red">Fragment area:</text>
                    <text x="10" y="25" font-family="Arial, sans-serif" font-size="11" fill="red">
                        <xsl:value-of select="format-number($fragment/area, '#,###')"/> px²
                    </text>
                </g>
                
                <!-- Legend -->
                <g transform="translate(20, 20)">
                    <rect x="0" y="0" width="200" height="80" fill="white" stroke="black" stroke-width="1" opacity="0.9"/>
                    <text x="10" y="20" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Legend:</text>
                    <rect x="10" y="30" width="20" height="15" fill="rgba(100, 150, 200, 0.3)" stroke="rgb(50, 100, 150)" stroke-width="2"/>
                    <text x="35" y="42" font-family="Arial, sans-serif" font-size="12">Paragraphs</text>
                    <line x1="10" y1="55" x2="30" y2="55" stroke="red" stroke-width="3"/>
                    <text x="35" y="60" font-family="Arial, sans-serif" font-size="12">Fragment boundary</text>
                </g>
            </svg>
        </xsl:result-document>
    </xsl:template>

    <xsl:template name="get_values">
        <xsl:param name="points_string"/>

        <!-- extract point values from string -->
        <xsl:variable name="points">
            <xsl:call-template name="get_points">
                <xsl:with-param name="points_string" select="$points_string"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:copy-of select="$points"/>

        <!-- calculate area of the polygon -->
        <xsl:call-template name="get_polygon_area">
            <xsl:with-param name="points" select="$points"/>
        </xsl:call-template>

    </xsl:template>

    <!-- extract point values from string -->
    <xsl:template name="get_points">
        <xsl:param name="points_string"/>
        <xsl:for-each select="tokenize($points_string, ' ')">
            <point n="{position()}">
                <x>
                    <xsl:value-of select="tokenize(., ',')[1]"/>
                </x>
                <y>
                    <xsl:value-of select="tokenize(., ',')[2]"/>
                </y>
            </point>
        </xsl:for-each>
    </xsl:template>

    <!-- calculate area of the polygon -->
    <xsl:template name="get_polygon_area">
        <xsl:param name="points"/>
        <xsl:variable name="scalar">
            <xsl:for-each select="$points/point">
                <xsl:choose>
                    <xsl:when test="position() != last()">
                        <xsl:variable name="x1" select="./x"/>
                        <xsl:variable name="y1" select="./y"/>
                        <xsl:variable name="x2" select="./following::x[1]"/>
                        <xsl:variable name="y2" select="./following::y[1]"/>

                        <xsl:variable name="x1y2" select="$x1 * $y2"/>
                        <xsl:variable name="y1x2" select="$y1 * $x2"/>

                        <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2"/>

                        <value n="{position()}">
                            <xsl:value-of select="$x1y2-y1x2"/>
                        </value>

                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="x1" select="./x"/>
                        <xsl:variable name="y1" select="./y"/>
                        <xsl:variable name="x2" select="/point[1]/x"/>
                        <xsl:variable name="y2" select="/point[1]/y"/>

                        <xsl:variable name="x1y2" select="$x1 * $y2"/>
                        <xsl:variable name="y1x2" select="$y1 * $x2"/>

                        <xsl:variable name="x1y2-y1x2" select="$x1y2 - $y1x2"/>

                        <value n="{position()}">
                            <xsl:value-of select="$x1y2-y1x2"/>
                        </value>

                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </xsl:variable>
        <area unit="px">
            <xsl:value-of select="format-number(sum($scalar/value) div 2, '#')"/>
        </area>
    </xsl:template>

</xsl:stylesheet>
