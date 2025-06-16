# ======================= CONFIGURATION ===========================
TARGET_SPECIFICATIONS = ["DIR's", "EDS's"]  # Example: ["DIR", "EDS"]; leave empty to process all
MOTIVE = "generates"
# ================================================================

import re
import Visure

def Visure_beforeCreateBaseline(bl, lBaselineID):
    try:
        bl.Trace_INFO("==== Starting ALL Traceability Passes Before Baseline ====")

        # Config for all 5 modes
        traceability_modes = {
            1: {
                "description": "Parent-child via 'parent req' & 'driving requirement'",
                "fields": ["Parent Req.", "Driving Requirement"],
                "regex": r"(F\.)\w+(\.\w+)?"
            },
            2: {
                "description": "DIR/EDS in 'reference'",
                "fields": ["Reference"],
                "regex": r"(F\.)\w+(\.\w+)?"
            },
            3: {
                "description": "10 CFR in 'reference'",
                "fields": ["Reference"],
                "regex": r"^\d{1,4} CFR \d{1,4}(\.\d+(\([a-zA-Z0-9]+\))?(\([a-zA-Z0-9]+\))?)?$"
            },
            4: {
                "description": "NCS Control references in 'reference'",
                "fields": ["Reference"],
                "regex": r"^[A-Za-z]{5}-[A-Za-z]{4}-[0-9]{3,4}-(?:[0-9]{1,5}\.){1,4}[0-9]{1,5}$"
            },
            5: {
                "description": "IROFS in 'description'",
                "fields": ["Description"],
                "regex": r"^[A-Z0-9]{2,4}[-\s][A-Z0-9]{1,3}$"
            }
        }

        # Get relationship type ID
        rel_type_id = bl.GetRelationshipTypeID(MOTIVE)
        if rel_type_id == -1:
            bl.Trace_WARNING(f"Relationship type '{MOTIVE}' not found.")
            return True

        # Cache all elements and index by Code
        all_element_ids = bl.ReadElements_L()
        all_elements_by_code = {}
        for lID in all_element_ids:
            if not bl.ExistsElement(lID, 0):
                continue
            item = bl.item(lID)
            all_elements_by_code[item.code.strip()] = item

        for mode in range(1, 6):
            config = traceability_modes[mode]
            bl.Trace_INFO(f"---- Starting Trace Mode {mode}: {config['description']} ----")
            regex = config["regex"]

            for lID in all_element_ids:
                if not bl.ExistsElement(lID, 0):
                    continue
                item = bl.item(lID)

                # Check specification filter
        if TARGET_SPECIFICATIONS:
            in_spec = False
            spec_id_to_name = {}
            for spec_name in TARGET_SPECIFICATIONS:
                spec_id = bl.GetSpecificationID(spec_name)
                spec_id_to_name[spec_id] = spec_name
                if item.belongsToSpecification(spec_id):
                    in_spec = True
                    break
                if not in_spec:
                    continue
        else:
            spec_id_to_name = {}

        # ========== Mode 1: Dynamic field selection ==========
        if mode == 1:
            item_spec_id = item.specification_id
            spec_name = spec_id_to_name.get(item_spec_id, "")
            if spec_name == "DIR's":
                fields_to_check = ["Parent Req."]
            elif spec_name == "EDS's":
                fields_to_check = ["Driving Requirement"]
            else:
                fields_to_check = config["fields"]
        else:
            fields_to_check = config["fields"]

        for field in fields_to_check:
            if not item.has_attribute(field):
                continue
            attr = bl.attribute(field)
            raw = str(item.value(attr.id)).strip()
            if not raw:
                continue

            if mode == 1:
                # Direct Code matching
                candidates = re.split(r"[,\n;]", raw)
                for token in candidates:
                    ref_code = token.strip()
                    if ref_code in all_elements_by_code:
                        target = all_elements_by_code[ref_code]
                        bl.CreateAssociationLink(item.id, target.id, rel_type_id)
                        bl.Trace_INFO(f"[{item.code}] --(direct)--> [{ref_code}]")
            else:
                # Regex matching
                for match in re.findall(regex, raw, flags=re.MULTILINE):
                    ref_code = match if isinstance(match, str) else (match[0] if match else None)
                    if not ref_code:
                        continue
                    ref_code = ref_code.strip()
                    if ref_code in all_elements_by_code:
                        target = all_elements_by_code[ref_code]
                        bl.CreateAssociationLink(item.id, target.id, rel_type_id)
                        bl.Trace_INFO(f"[{item.code}] --(regex)--> [{ref_code}]")

            bl.Trace_INFO(f"---- Trace Mode {mode} Complete ----")

        bl.Trace_INFO("==== All Traceability Passes Completed ====")

    except Exception as e:
        bl.Trace_ERROR(f"Unhandled error in traceability process: {e}")

    return True
