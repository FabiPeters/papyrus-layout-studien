from pathlib import Path
import xml.etree.ElementTree as ET

ns = {"page": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"}

def column_is_usable(element_attributes: dict) -> bool:
    bool = True if "type:column;" in element_attributes["custom"] else False
    return bool
    #return "type:column;" in element_attributes["custom"]

def get_columns(element: ET.Element) -> list[tuple]:
    pass

def get_lines(element: ET.Element) -> list[tuple]:
    pass

page_xml_path = Path("page_xml/")

page_xml_list = list(page_xml_path.glob("**/page/*.xml"))

tree = ET.parse(page_xml_list[4])
root = tree.getroot()

column_data = {}
for text_region in root.findall(".//page:TextRegion", ns):
    if column_is_usable(text_region.attrib):
        print(text_region.attrib)
    id = text_region.attrib["id"]
    column_data.update({id: {"column_coords": (), "lines": {}}})
    coords = tuple(text_region.find("page:Coords", ns).attrib["points"].split(" "))
    # print(coords)
    if len(coords) > 4:
        print(f"TextRegion {id} has too many points!")
        continue
    elif len(coords) < 4:
        print(f"TextRegion {id} has too few points!")
        continue


    column_data[id].update({"column_coords": coords})
print(column_data)
    # if "type:column;" in text_region.attrib["custom"]:
    #     print(text_region.attrib)
