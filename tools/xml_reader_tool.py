from langchain.tools import tool
from lxml import etree
from typing import Dict
import json


@tool
def read_xml_invoice(file_path: str) -> Dict[str, str]:
    """
    Parse un fichier XML de facture électronique (UBL ou Factur-X).
    Retourne les éléments XML sous forme de dictionnaire JSON.
    """
    tree = etree.parse(file_path)
    root = tree.getroot()

    def element_to_dict(elem) -> Dict:
        result = {}
        if elem.text and elem.text.strip():
            result["_text"] = elem.text.strip()
        for key, value in elem.attrib.items():
            result[f"@{key}"] = value
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            child_data = element_to_dict(child)
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_data)
            else:
                result[tag] = child_data
        return result

    data = element_to_dict(root)
    return {
        "xml_parse": json.dumps(data, ensure_ascii=False, indent=2),
        "racine": root.tag.split("}")[-1] if "}" in root.tag else root.tag,
    }
