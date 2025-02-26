class GasConfig:

    GIE_AGSI_API = "https://agsi.gie.eu/"
    GIE_ALSI_API = "https://alsi.gie.eu/"
    GIE_IPP_API = "https://iip.gie.eu/"

    facility_type_dict = {
        "DSR": "Depleted Field Storage",
        "ASR": "Aquifer Storage",
        "ASF": "Salt Cavern Storage",
        "SRC": "Rock Cavern Storage",
        "GRP": "Virtual Storage Group",
        "SSO": "Storage System Operator"
    }

    gie_definition_dict = {
        "GIE": "Gas Infrastructure Europe",
        "UMM": "Urgent Market Message",
        "IIP": "Inside Information Platform",
        "ACER": "The European Union Agency for the Cooperation of Energy Regulators"
    }


class PowerConfig:
    raise NotImplementedError('Class not implemented')
