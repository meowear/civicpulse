from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Locality:
    zone: str
    latitude: float
    longitude: float
    population_density_score: float


LOCALITIES: dict[str, Locality] = {
    "ameerpet": Locality("Central", 17.4375, 78.4483, 8.4),
    "banjara hills": Locality("Central", 17.4126, 78.4482, 7.6),
    "jubilee hills": Locality("Central", 17.4326, 78.4071, 7.4),
    "khairatabad": Locality("Central", 17.4118, 78.4622, 8.0),
    "lakdikapul": Locality("Central", 17.4046, 78.4652, 8.2),
    "abids": Locality("Central", 17.3898, 78.4766, 8.8),
    "koti": Locality("Central", 17.3858, 78.4836, 8.9),
    "nampally": Locality("Central", 17.3889, 78.4678, 8.6),
    "himayatnagar": Locality("Central", 17.4049, 78.4821, 8.3),
    "narayanguda": Locality("Central", 17.3983, 78.4896, 8.3),
    "musheerabad": Locality("Central", 17.4196, 78.4994, 8.4),
    "mehdipatnam": Locality("Central", 17.3949, 78.4398, 8.2),
    "mehdipatnam flyover": Locality("Central", 17.3949, 78.4398, 8.2),
    "asifnagar": Locality("Central", 17.3852, 78.4567, 8.1),
    "masab tank": Locality("Central", 17.4030, 78.4529, 8.0),
    "basheerbagh": Locality("Central", 17.4015, 78.4775, 8.4),
    "liberty": Locality("Central", 17.4062, 78.4808, 8.5),
    "sultan bazaar": Locality("Central", 17.3866, 78.4816, 8.7),
    "rtc cross roads": Locality("Central", 17.4076, 78.4962, 8.6),
    "chikkadpally": Locality("Central", 17.4029, 78.4977, 8.4),
    "domalguda": Locality("Central", 17.4107, 78.4815, 8.2),
    "vidyanagar": Locality("Central", 17.4065, 78.5083, 8.2),
    "nallakunta": Locality("Central", 17.3986, 78.5077, 8.5),
    "punjagutta": Locality("Central", 17.4260, 78.4518, 8.6),
    "somajiguda": Locality("Central", 17.4235, 78.4584, 8.2),
    "s r nagar": Locality("Central", 17.4437, 78.4458, 8.5),
    "sr nagar": Locality("Central", 17.4437, 78.4458, 8.5),
    "erragadda": Locality("Central", 17.4570, 78.4262, 8.4),
    "yousufguda": Locality("Central", 17.4354, 78.4277, 8.1),
    "necklace road": Locality("Central", 17.4239, 78.4738, 7.8),
    "tank bund": Locality("Central", 17.4156, 78.4747, 8.0),
    "tolichowki": Locality("Central", 17.3984, 78.4138, 7.8),
    "langar houz": Locality("Central", 17.3829, 78.4227, 7.8),
    "charminar": Locality("South", 17.3616, 78.4747, 9.0),
    "malakpet": Locality("South", 17.3736, 78.5150, 8.1),
    "saidabad": Locality("South", 17.3587, 78.5114, 8.1),
    "santosh nagar": Locality("South", 17.3477, 78.5086, 8.2),
    "chandrayangutta": Locality("South", 17.3058, 78.4749, 8.2),
    "bahadurpura": Locality("South", 17.3574, 78.4564, 8.4),
    "attapur": Locality("South", 17.3687, 78.4305, 7.7),
    "rajendranagar": Locality("South", 17.3200, 78.4033, 7.0),
    "barkas": Locality("South", 17.3123, 78.4833, 7.5),
    "falaknuma": Locality("South", 17.3301, 78.4675, 7.3),
    "old city": Locality("South", 17.3606, 78.4740, 8.8),
    "yakutpura": Locality("South", 17.3548, 78.4900, 8.6),
    "moghalpura": Locality("South", 17.3580, 78.4805, 8.7),
    "shalibanda": Locality("South", 17.3518, 78.4713, 8.5),
    "hussaini alam": Locality("South", 17.3619, 78.4667, 8.5),
    "purani haveli": Locality("South", 17.3663, 78.4835, 8.4),
    "jahanuma": Locality("South", 17.3333, 78.4607, 8.0),
    "kishanbagh": Locality("South", 17.3481, 78.4303, 7.9),
    "mir alam": Locality("South", 17.3492, 78.4420, 7.8),
    "kukatpally": Locality("West", 17.4933, 78.3995, 9.2),
    "kukatpally metro": Locality("West", 17.4933, 78.3995, 9.2),
    "miyapur": Locality("West", 17.4967, 78.3615, 8.2),
    "hitech city": Locality("West", 17.4486, 78.3908, 8.0),
    "hitex": Locality("West", 17.4697, 78.3762, 7.8),
    "kondapur": Locality("West", 17.4638, 78.3647, 8.1),
    "gachibowli": Locality("West", 17.4401, 78.3489, 7.1),
    "financial district": Locality("West", 17.4142, 78.3428, 6.8),
    "madhapur": Locality("West", 17.4483, 78.3915, 8.0),
    "ikea": Locality("West", 17.4386, 78.3755, 7.6),
    "raidurg": Locality("West", 17.4269, 78.3886, 7.4),
    "manikonda": Locality("West", 17.4056, 78.3763, 7.9),
    "alkapur": Locality("West", 17.3952, 78.3714, 7.4),
    "narsingi": Locality("West", 17.3881, 78.3578, 7.0),
    "tellapur": Locality("West", 17.4645, 78.2711, 6.8),
    "moosapet": Locality("West", 17.4707, 78.4252, 8.5),
    "borabanda": Locality("West", 17.4539, 78.4128, 8.2),
    "sanathnagar": Locality("West", 17.4568, 78.4431, 8.2),
    "hafeezpet": Locality("West", 17.4848, 78.3578, 8.0),
    "chanda nagar": Locality("West", 17.4938, 78.3321, 8.0),
    "serilingampally": Locality("West", 17.4837, 78.3158, 7.9),
    "lingampally": Locality("West", 17.4863, 78.3170, 7.8),
    "nizampet": Locality("West", 17.5187, 78.3853, 8.1),
    "pragathi nagar": Locality("West", 17.5168, 78.3943, 8.0),
    "bachupally": Locality("West", 17.5504, 78.3889, 7.6),
    "patancheru": Locality("West", 17.5302, 78.2645, 7.4),
    "lb nagar": Locality("East", 17.3457, 78.5522, 8.5),
    "uppal": Locality("East", 17.4059, 78.5591, 8.1),
    "dilsukhnagar": Locality("East", 17.3687, 78.5247, 8.7),
    "kothapet": Locality("East", 17.3682, 78.5462, 8.4),
    "saroornagar": Locality("East", 17.3567, 78.5350, 8.2),
    "hayathnagar": Locality("East", 17.3279, 78.6055, 7.2),
    "amberpet": Locality("East", 17.3910, 78.5169, 8.3),
    "ramanthapur": Locality("East", 17.3976, 78.5389, 8.0),
    "habsiguda": Locality("East", 17.4128, 78.5422, 8.0),
    "nacharam": Locality("East", 17.4291, 78.5583, 7.7),
    "boduppal": Locality("East", 17.4139, 78.5783, 7.7),
    "nagole": Locality("East", 17.3715, 78.5692, 8.2),
    "vanasthalipuram": Locality("East", 17.3307, 78.5751, 8.1),
    "chaitanyapuri": Locality("East", 17.3699, 78.5328, 8.5),
    "moosarambagh": Locality("East", 17.3722, 78.5124, 8.3),
    "peerzadiguda": Locality("East", 17.4058, 78.6008, 7.7),
    "medipally": Locality("East", 17.4087, 78.6041, 7.6),
    "mansoorabad": Locality("East", 17.3498, 78.5706, 8.0),
    "secunderabad": Locality("Secunderabad", 17.4399, 78.4983, 9.0),
    "secunderabad station": Locality("Secunderabad", 17.4336, 78.5016, 9.1),
    "begumpet": Locality("Secunderabad", 17.4440, 78.4629, 8.4),
    "paradise": Locality("Secunderabad", 17.4437, 78.4873, 8.6),
    "tarnaka": Locality("Secunderabad", 17.4275, 78.5385, 8.0),
    "marredpally": Locality("Secunderabad", 17.4519, 78.5087, 8.1),
    "bowenpally": Locality("Secunderabad", 17.4705, 78.4859, 8.0),
    "karkhana": Locality("Secunderabad", 17.4589, 78.4980, 8.2),
    "trimulgherry": Locality("Secunderabad", 17.4725, 78.5146, 7.9),
    "lalapet": Locality("Secunderabad", 17.4315, 78.5297, 8.3),
    "warasiguda": Locality("Secunderabad", 17.4269, 78.5128, 8.4),
    "padmarao nagar": Locality("Secunderabad", 17.4257, 78.5052, 8.4),
    "chilakalguda": Locality("Secunderabad", 17.4337, 78.5056, 8.5),
    "malkajgiri": Locality("North", 17.4474, 78.5265, 8.6),
    "alwal": Locality("North", 17.5047, 78.5033, 7.2),
    "sainikpuri": Locality("North", 17.4898, 78.5496, 7.3),
    "kompally": Locality("North", 17.5418, 78.4814, 7.1),
    "jeedimetla": Locality("North", 17.5151, 78.4555, 7.5),
    "quthbullapur": Locality("North", 17.5014, 78.4575, 7.8),
    "kapra": Locality("North", 17.4859, 78.5651, 7.4),
    "ecil": Locality("North", 17.4697, 78.5724, 7.5),
    "balanagar": Locality("North", 17.4764, 78.4483, 8.0),
    "suchitra": Locality("North", 17.5087, 78.4800, 7.6),
    "suraram": Locality("North", 17.5417, 78.4381, 7.5),
    "chintal": Locality("North", 17.5104, 78.4581, 7.9),
    "gajularamaram": Locality("North", 17.5311, 78.4153, 7.5),
    "shamirpet": Locality("North", 17.5945, 78.5732, 6.8),
}


UNKNOWN_LOCALITY = Locality("Unknown", 17.3850, 78.4867, 5.0)
ALIASES: dict[str, str] = {
    "hi tech city": "hitech city",
    "hitec city": "hitech city",
    "l b nagar": "lb nagar",
    "l.b. nagar": "lb nagar",
    "saroor nagar": "saroornagar",
    "qutubullapur": "quthbullapur",
    "khairtabad": "khairatabad",
    "toli chowki": "tolichowki",
    "rtc x roads": "rtc cross roads",
    "rtc x road": "rtc cross roads",
    "rtc crossroads": "rtc cross roads",
    "s r nagar": "sr nagar",
    "sanath nagar": "sanathnagar",
    "chandanagar": "chanda nagar",
    "chanda nagar": "chanda nagar",
    "bhel": "patancheru",
    "triulgherry": "trimulgherry",
    "tirumalagiri": "trimulgherry",
    "tirumalgherry": "trimulgherry",
}


def normalize_location_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for alias, canonical in ALIASES.items():
        normalized = re.sub(rf"\b{re.escape(alias)}\b", canonical, normalized)
    return normalized


def extract_known_locality(text: str) -> str | None:
    normalized = normalize_location_text(text)
    for landmark in sorted(LOCALITIES, key=len, reverse=True):
        if landmark in normalized:
            return landmark
    return None


def resolve_locality(text: str) -> Locality:
    landmark = extract_known_locality(text)
    if landmark:
        return LOCALITIES[landmark]
    return UNKNOWN_LOCALITY
