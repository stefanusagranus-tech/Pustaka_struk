"""
Dictionary PLU -> Nama Item
Dibangun manual dari daftar PLU toko (hardcode)
Last updated: 29/09/2026

Cara pakai:
    from utils.plu_dict import PLU_NAMES, get_nama_plu, get_plu_normalized
    
    nama = get_nama_plu(4279272)   # -> "RINSO RYL GL500" (auto-normalisasi)
    plu_norm = get_plu_normalized(4279272)  # -> 427927
"""

PLU_NAMES = {
    # ============================================================
    # GRUP 1: MAITOS, CHUBA, NABATI
    # ============================================================
    401609: "MR HOTTEST MAITOS TBLD 120/140G",
    401681: "MR HOTTEST MAITOS TBBQ 120/140G",
    451111: "MR HOTTEST MAITOS MIGRG120/125G",
    406546: "CHUBA CASSAVA CHILI BLD120/125G",
    406547: "CHUBA CASSAVA BBQ 120/125G",
    445327: "CHUBA CASSAVA CHEESE 120/125G",
    440071: "NABATI WFR GOGUMA 110G",
    400618: "RICHOCO WFR NABATI 110G",
    400619: "RICHEESE WFR NABATI 110G",
    461389: "NABATI WFR STR CHEESECAKE 110G",

    # ============================================================
    # GRUP 2: LE MINERALE, PEPSODENT JUMBO
    # ============================================================
    990055: "LE MINERALE AIR MNRL PET 600ML",
    404759: "LE MINERALE AIR MNRL PET 1500ML",
    126475: "PEPSODENT PG ECONOMY JUMBO 225G",

    # ============================================================
    # GRUP 3: SOSOFT
    # ============================================================
    429742: "SOSOFT LIQ DET ROSELILY 700ML",
    431407: "SOSOFT LIQ DET SAKURA 700ML",
    434164: "SOSOFT LIQ DET FREESIA 700ML",
    444215: "SOSOFT LIQ DET PEONY 700ML",
    452219: "SOSOFT LIQ DET FLORAL LILY 700M",

    # ============================================================
    # GRUP 4: VASELINE
    # ============================================================
    116502: "VASELINE HBL HLTY BRGHT 200ML",
    414502: "VASELINE HBL HW FRESH&FAIR200ML",
    143958: "VASELINE HBL ALOE SOOTHE 200ML",
    420813: "VASELINE B.SERUM SOFT GLW 180ML",
    432392: "VASELINE B.SRM HJB SPF20 180ML",
    451086: "VASELINE B.SRM GLUTA FLAW 180ML",
    451087: "VASELINE B.SRM GLUTA DEWY 180ML",

    # ============================================================
    # GRUP 5: FF UHT PF
    # ============================================================
    115957: "FF UHT PF COKELAT TP 225ML",
    115958: "FF UHT PF STROBERI TP 225ML",
    115959: "FF UHT PF F.CREAM TP 225ML",

    # ============================================================
    # GRUP 6: PIATTOS
    # ============================================================
    220170: "J&J PIATTOS SAPI PGG 65G",
    220171: "J&J PIATTOS RUMPUT LAUT 65G",
    414489: "J&J PIATTOS SBL GEPREK 65G",
    459536: "J&J PIATTOS OSENG MERCON 69G",
    427854: "J&J PIATTOS SAPI PGG 115G",
    435192: "J&J PIATTOS SBL GEPREK 115G",
    459535: "J&J PIATTOS RUMPUT LAUT 115G",

    # ============================================================
    # GRUP 7: SILVER QUEEN
    # ============================================================
    1352: "SILVER QUEEN CASHEW 52G",
    1595: "SILVER QUEEN ALMOND 52G",

    # ============================================================
    # GRUP 8: INDOMILK
    # ============================================================
    140249: "INDOMILK UHT F.CREAM TP 950ML",
    140248: "INDOMILK UHT COKELAT TP 950ML",
    401705: "INDOMILK BANANA TP 180ML",
    460482: "INDOMILK MATCHA TP 180ML",
    431042: "INDOMILK KKM CHOCO PCH 535G",
    414212: "INDOMILK KKM PUTIH PCH 535G",

    # ============================================================
    # GRUP 9: SGM EKSPLOR
    # ============================================================
    120766: "SGM EKSPLOR 1+ MADU BOX 900G",
    120767: "SGM EKSPLOR 1+ VANILA BOX 900G",
    120771: "SGM EKSPLOR 3+ VANILA BOX 900G",
    120772: "SGM EKSPLOR 3+ MADU BOX 900G",
    120773: "SGM EKSPLOR 3+ COKELAT BOX 900G",
    200219: "SGM EKSPLOR 5+ MADU BOX 900G",
    200218: "SGM EKSPLOR 5+ COKELAT BOX 900G",
    403419: "SGM EKSPLOR SOYA MADU BOX 700G",
    210101: "SGM EKSPLOR SOYA VANILA BOX700G",

    # ============================================================
    # GRUP 10: LACTOGROW
    # ============================================================
    110893: "LACTOGROW PRO1+ PLAIN BOX735G",
    210016: "LACTOGROW PRO 1+ MADU BOX735G",
    412361: "LACTOGROW PRO 1+ VNL BOX 735G",
    125486: "LACTOGROW PRO 3+ VNL BOX 735G",
    210086: "LACTOGROW PRO 3+ MADU BOX 735G",

    # ============================================================
    # GRUP 11: LANG MINYAK (KAYU PUTIH, TELON)
    # ============================================================
    406076: "LANG M.KAYU PUTIH PLUS 120ML",
    405727: "LANG M.KAYU PUTIH PLUS 60ML",
    5330: "LANG M.KAYU PUTIH 120ML",
    5329: "LANG M.KAYU PUTIH 60ML",
    433294: "CAPLANG TELON LANG 150ML",
    312043: "LANG M.TELON PLUS 150ML",
    100850: "LANG M.TELON 60ML",
    128168: "LANG M.TELON PLUS 60ML",
    105076: "GPU MINYAK URUT SEREH 60ML",

    # ============================================================
    # GRUP 12: CAT CHOIZE & ME-O
    # ============================================================
    424860: "CAT CHOIZE+ DRY ADULT 500G",
    429219: "CAT CHOIZE+ DRY KITTEN 450G",
    437733: "CAT CHOIZE+ DRY ADT TN&MACK500G",
    431399: "ME-O CAN ADULT TUNA JL400G",
    437883: "ME-O CAN KITTEN TUNA JL 400G",
    412597: "ME-O CRM TREAT SALMON 4X15G",
    439361: "ME-O CRMY TREAT TUNA 4X15G",
    431401: "ME-O CRMY CKN&LIVER 4X15G",

    # ============================================================
    # GRUP 13: POSH
    # ============================================================
    412951: "POSH WMN RO WHITENING 50ML1",
    412952: "POSH WMN RO ANTI STAIN 50ML",
    432543: "POSH WMN RO HIJAB CHIC 50ML",
    426205: "POSH MEN RO ACT COOL 50ML",
    426834: "POSH MEN RO ACT SPORT 50ML",
    404619: "POSH MEN BS COOL BLUE 150ML",
    412950: "POSH MEN BS RED EXTREME 150ML",
    417410: "POSH HIJAB BS GREEN BLSSM 150ML",
    417412: "POSH HIJAB BS PURPLE WISH 150ML",
    448763: "POSH MEN BS ICE AQUA FROST150ML",

    # ============================================================
    # GRUP 14: NUVO
    # ============================================================
    320826: "NUVO BW MILD PROTECT 400ML",
    321094: "NUVO BW TOTAL PROTECT 400ML",
    427393: "NUVO BW SAKINAH ZAITUN 400ML",
    444265: "NUVO ICE COOL PROTECT BW 400ML",
    425796: "NUVO BW TOTAL PROTECT 800ML",
    432934: "NUVO BW MILD PROTECT 800ML",
    442232: "NUVO FAMILY BW KUNING 800ML",

    # ============================================================
    # GRUP 15: SEDAAP
    # ============================================================
    425637: "SEDAAP MIE AYAM JERIT CUP 75G",
    431884: "SEDAAP MIE BAKSO BLEDUK CUP 77G",
    123274: "SEDAAP MIE SOTO CUP 81G",
    190000: "SEDAAP MIE KARI SPS CUP 81G",
    445334: "SEDAAP RAWIT KARI MERCON 79G",
    459385: "SEDAAP MIE SPICY LAKSA CUP 86G",
    123273: "SEDAAP MIE GRG CUP 85G",
    417653: "SEDAAP MIE KOREAN S CKN CUP81G",
    426794: "SEDAAP MIE SINGAPORE LAKSA 83G",
    224207: "SEDAAP MIE AYAM BAWANG 71G",
    113469: "SEDAAP MIE KARI SPECIAL 75G",
    439738: "SEDAAP MIE AYAM JERIT RAWIT 77G",
    419942: "SEDAAP MIE KOREAN SPICY SOUP77G",
    224210: "SEDAAP MIE KARI AYAM 72G (KZ)",
    415665: "SEDAAP MIE GRG 5X91G",
    415666: "SEDAAP MIE SOTO 5X76G",
    451434: "SEDAAP MIE AYAM BAWANG 5X71G",
    109669: "SEDAAP KECAP MNS REF 700G",
    421437: "SEDAAP KCP KDLHTM PCH 725G",
    453743: "SEDAAP KCP KDLHTM SPC PACK 725G",

    # ============================================================
    # GRUP 16: SHINZU'I
    # ============================================================
    117707: "SHINZU''I BW KIREI 380G/380ML",
    143153: "SHINZU''I BW MATSU 380G/380ML",
    320875: "SHINZU''I BW SAKURA 380G/380ML",
    426561: "SHINZU''I BW KIREI 725G/725ML",
    441152: "SHINZU''I BW SAKURA 725G/725ML",

    # ============================================================
    # GRUP 17: LOREAL
    # ============================================================
    451890: "LOREAL SHP GLYCOLIC GLOSS 200ML",
    451891: "LOREAL COND GLYCOLIC GLOSS 175M",
    451892: "LOREAL SHP FALL RESIST 200ML",
    451893: "LOREAL COND FALL RSST 175ML(HP)",
    451894: "LOREAL SHP HYALURON PURE 200ML",
    452220: "LOREAL EXTRAORDINARY OIL 30ML",

    # ============================================================
    # GRUP 18: CIPTADENT
    # ============================================================
    427374: "CIPTADENT PG FRESH MINT 225 GR",
    437623: "CIPTADENT PG COOL MINT 225 GR",
    450864: "CIPTADENT PG FRESH MAXI 190GR",
    320417: "CIPTADENT PG HERBAL 190G",
    422397: "CIPTADENT SG PERFECT CARE 3S",

    # ============================================================
    # GRUP 19: NIPIS MADU
    # ============================================================
    438350: "NIPIS MADU LIME SODA PET 330ML",
    461067: "NIPIS MADU LIME SODA PET 1L",

    # ============================================================
    # GRUP 20: OATSIDE
    # ============================================================
    431226: "OATSIDE BARISTA BLEND 1L",
    442189: "OATSIDE BARISTABLEND STRAW200ML",

    # ============================================================
    # GRUP 21: PASEO
    # ============================================================
    415852: "PASEO B.WIPES JOJOBA OIL 2X50S",
    400017: "PASEO BABY TISSUE PURE SOFT130S",
    163865: "PASEO FAC TISSUE SFT510PLY/250S",

    # ============================================================
    # GRUP 22: KAHF
    # ============================================================
    423646: "KAHF FF ENERGIZING&BRIGHT 100ML",
    423647: "KAHF FF OIL&ACNE CARE 100ML",
    427902: "KAHF FF SCRUB EXFOLIATING100ML",
    445967: "KAHF FF ACN&POR CLNS SCRB 100ML",
    432462: "KAHF FF OIL&COMEDO 100ML",
    450862: "KAHF FF ACNE GEL 100ML",
    450863: "KAHF FF BRIGHT GEL 100ML",
    427249: "KAHF SUNSCREEN MOIS SPF30 30ML",
    441818: "KAHF MEN RO EXTRA DRY 45ML",
    441842: "KAHF MEN RO COOLING POWER 45ML",
    446821: "KAHF POMADE SLEEK CLASSY 70G",

    # ============================================================
    # GRUP 23: WARDAH
    # ============================================================
    422669: "WARDAH UV SHILED SPF50 30ML(HB)",
    424126: "WARDAH UV SHIELD SPF35 40ML",
    439633: "WARDAH UV SHIELD SPF50+25ML",
    444148: "WARDAH UV SHLD ACNE SPF35++35ML",
    444489: "WARDAH UV ACNE SPF 50 25ML",
    448861: "WARDAH MOIST GEL SYRDNC 399 30G",
    403227: "WARDAH FF CRYTL SECRET AHA100ML",
    408127: "WARDAH FF C-DEFENSE 100ML",
    411988: "WARDAH FF BRIGHT+OIL 100ML",
    411989: "WARDAH FF BRIGHT+SMOOTH 100ML",
    421494: "WARDAH FF LG WHIP 100 ML",

    # ============================================================
    # GRUP 24: DOWNY
    # ============================================================
    450595: "DOWNY MILKY TOUCH 500ML",
    410599: "DOWNY FLORAL PINK REF 550ML",
    404631: "DOWNY SUNRISE FRS REF 550ML",
    407608: "DOWNY PASSION REF 550ML",
    407607: "DOWNY MYSTIQUE REF 550ML",

    # ============================================================
    # GRUP 25: RINSO
    # ============================================================
    444925: "RINSO DET JPNSE PEACH 1.4KG",
    451339: "RINSO DET PURE 1.4KG",
    451889: "RINSO DET ROSE FRESH 1.4KG",
    403543: "RINSO DET MOLTO 700G",
    408031: "RINSO DET MOLTO PURPLE 700G",
    421062: "RINSO DET MOLTO JPNSE 700/770G",

    # ============================================================
    # GRUP 26: MAKUKU
    # ============================================================
    448764: "MAKUKU TAPED COMFORT FIT NB-40",
    440195: "MAKUKU PANTS CMFRT FIT M30/28",
    440196: "MAKUKU PANTS COMFORT FIT L26",
    443579: "MAKUKU PANTS COMFORT FIT XXL22",
    440197: "MAKUKU PANTS COMFORT FIT XL24",
    446286: "MAKUKU PANTS D.CARE L28+4/28+6",
    446287: "MAKUKU PANTS D.CARE XL24+2/24+4",

    # ============================================================
    # GRUP 27: BAYGON
    # ============================================================
    15071: "BAYGON AEO CITRUS FRESH 600+75M",
    403380: "BAYGON AEO FLOWER GRDN 600+75ML",
    416401: "BAYGON AEO CHERRY BLOSSOM 600ML",
    433288: "BAYGON AEO JAPANESE PEACH 600ML",
    408678: "BAYGON AEO LAVENDER 400ML",
    450963: "BAYGON AE CITRUS FRESH 400ML",

    # ============================================================
    # GRUP 28: SUNLIGHT
    # ============================================================
    432389: "SUNLIGHT KRN STRWB REF600ML",
    433323: "SUNLIGHT JERUK NPS REF660G",
    434244: "SUNLIGHT DAUN MINT REF600ML",
    444497: "SUNLIGHT BIO NATURE REF 600ML",
    434243: "SUNLIGHT MNDR LOVE REF600ML",
    437941: "SUNLIGHT EXT LEMBUT REF 600ML",
    425602: "SUNLIGHT JERUK NIPIS 400G",
    451870: "SUNLIGHT JERUK NIPIS BTL 675G",
    451873: "SUNLIGHT BIO NATURE BRY BTL675G",
    451874: "SUNLIGHT BERRY & LIME BTL 675G",

    # ============================================================
    # GRUP 29: ROMA
    # ============================================================
    758: "ROMA MALKIST CRACKERS 105G",
    759: "ROMA CREAM CRACKERS 107G",
    120342: "ROMA MALKIST ABON CRKR 105G",
    466311: "ROMA MALKIST KELAPA KOPYOR 105G",
    120346: "SLAI O'LAI BISC STROBERI 128G",

    # ============================================================
    # GRUP 30: HAPPY NAPPY
    # ============================================================
    414932: "HAPPY NAPPY SMART PANTS M32",
    414933: "HAPPY NAPPY SMART PANTZ L28",
    416690: "HAPPY NAPPY SMART PANTS XL24",

    # ============================================================
    # GRUP 31: REBO KUACI
    # ============================================================
    120090: "REBO KUACI ORIGINAL 120G",
    123859: "REBO KUACI MILK 120G",
    220573: "REBO KUACI GREEN TEA 120G",
    413792: "REBO KUACI CARAMEL 120G",

    # ============================================================
    # GRUP 32: MITU
    # ============================================================
    117784: "MITU B.WIPES REG PINK BGF 50S",
    212838: "MITU B.WIPES GT POPOK BLUE 50S",
    402177: "MITU B.WIPES GT POPOK PURPLE50S",
    117783: "MITU B.WIPES ANTISEPTIC BGF 50S",

    # ============================================================
    # GRUP 33: KOPI & CANDY
    # ============================================================
    459459: "KAPAL API KOPI SPECIAL 250G",
    431255: "PIKOPI GULA AREN 9X22G",
    102323: "KIS CANDY CHERRY 75G",
    113227: "KIS CANDY GRAPE MINT 75G",
    230065: "KIS CANDY MINT APPLE PCH 75G",

    # ============================================================
    # GRUP 34: MISC PRODUK
    # ============================================================
    264136: "FRENCH FRIES 2000 PRM 24G",
    417804: "KANZLER SGL ORI 65G",
    417805: "KANZLER SGL KEJU 65G",
    417806: "KANZLER SGL MINI 65G",
    423992: "KANZLER SGL HOT 65G",
    435578: "KANZLER SGL GOCHUJANG 60G",
    459704: "KANZLER SGL TOM YUM 60G",
    419154: "PAROTI BAGELEN CHEESE 78G",
    419155: "PAROTI BAGELEN VANILLA 72G",
    421456: "ALFAMART FAC TISSUE400G",
    444388: "ENTRASOL STERIL OLIVE CAN 180ML",
    445222: "DOVE WMN RO SERUM COLLAGEN 45ML",
    448076: "HYDRO COCO LATTE CAN 220ML",
    453900: "DOVE BW MOISTURE RENEW 300G",
    453901: "DOVE BW PAMPERING CARE 300G",
    461251: "RTE NASIKUCING AYAM BMB BALI MD",
    461252: "RTE NASIKUCING TERI CABE IJO",
    461253: "RTE NASIKUCING AYAMSUWIR BLD MD",
    990149: "HYDRO COCO ORIGINAL PET 500ML",

    # ============================================================
    # GRUP 35: PLU SG (Serba Gratis)
    # ============================================================
    444755: "WOW SPAGETI CARBONARA 80G",
    444756: "WOW SPAGETI BOLOGNESE 76G",
    448657: "WOW SPAGETI AGLIO OLIO 75G",
    461599: "WOW SPAGETI GORENG 79G",
    441179: "MOM'S RECIPE SP TARO PCH 110G",
    110859: "MOM'S RECIPE SP MANGGA PCH 108G",
    213741: "OVALE FAC LOT PRFT LMNS 200ML",
    452835: "ELLIPS VIT HAIR MIST ME UP 50ML",
    453045: "RAMEN YES GRG YAKITORI 84G",
    453044: "RAMEN YES RAMEN CHICKEN 88G",
    428690: "KOOLFEVER DEWASA 1S",
    197589: "RAPIKA LAVENDER REF 300ML",
    415156: "RAPIKA SOFT SAKURA REF 300ML",
    454096: "RAPIKA EDP PURPLE 300ML (HC)",
    125431: "KOKO KRUNCH CUP 30G",
    125432: "MILO CEREAL CUP 30G",
    113852: "NUTRIVE BENECOL B.CRNT BTL100ML",
    200213: "NUTRIVE BENECOL LYCHEE BTL100ML",
    408055: "NUTRIVE BENECOL ORG BTL 100ML",
    113850: "NUTRIVE BENECOL STR BTL 100ML",
    460878: "ALFA AIR MNRL ONEPIECE FT 600ML",
    426512: "VIT AIR MNRL PET 550ML",
    459336: "PEPSODENT PG SNSTV EXP ORI 60G",
    460329: "PEPSODENT PG SNSTV EXP WHT 60G",
    453125: "PEPSODENT PG SNSTV EXP CPCR 60G",
    453252: "PEPSODENT PG GUM EXP WHTNG 60G",
    453126: "PEPSODENT PG SNSTV EXP FRSH 60G",
    452313: "ALFAMART CREAMY TREATS TUNA 4S",
    439558: "ALFA KITTEN CAT CHOIZE 70G",
    439557: "ALFA ADULT CAT CHOIZE 70G",
    444036: "ALFA DORAEMON KITTEN FOOD 70G",
    451060: "ALFA FAC TISSUE ONE PIECE 100S",
    421455: "ALFAMART FAC TISSUE ALBI 50'S",
    442078: "ALFA WIPES DISNEY BABY 20S",
    414495: "PROMINA BABY CRUNCH KEJU 20G",
    437950: "PROMINA BABY CRUNCH R.LAUT 20G",
    437951: "PROMINA BABY CRUNCH AYM BRKL20G",
    990150: "PRISTINE 8.6+ WTR PET 400ML",

    # ============================================================
    # GRUP 36: PLU PSM (Promo Serba Murah)
    # ============================================================
    435191: "OISHI KRAKER UDANG PEDAS 130G",
    429397: "OISHI RINBEE STK KEJU 130G",
    434880: "OISHI POPPY POP JGG BKR 130G",
    401632: "OISHI POPCORN CARAMEL 100G",
    401633: "OISHI POPCORN COKLAT 100G",
    434281: "OISHI POPCORN BUT CHEESE 100G",
    221623: "ABC KECAP MNS REF 685G",
    4504: "ABC SBL ASLI PET 130ML",
    4557: "ABC SBL EXT PEDAS PET 130ML",
    118380: "ABC SBL EXT PEDAS BTL 270ML",
    118379: "ABC SBL ASLI PET 270ML",
    440439: "ABC SBL EXTRM PDS PET 270ML",
    461159: "ABC KECAP HITAM MNS REF 550G",
    5867: "AQUA AIR MNRL PET 1500ML",
    5868: "AQUA AIR MNRL PET 600ML",
    401180: "FF SKM COKELAT PCH 535G",
    401181: "FF SKM PUTIH PCH 535G",
    120076: "FF UHTOMEGA COKELAT 6X110ML",
    120077: "FF UHTOMEGA STROBERI6X110ML",
    466031: "FF UHTOMEGA PLAIN 6X110ML",
    124226: "GLOW&LOVELY CREAM MULTI VIT 50G",
    400443: "GLOW&LOVELY FF MULTI VIT 100G",
    424005: "GLOW&LOVELY FF VIT C GLOW 100G",
    434414: "GLOW&LOVELY SPF35 + VIT C 40G",
    465935: "GLOW&LOVELY SNSC SPF50 30ML(HB)",
    454047: "GLOW&LOVELY FW GEL BRGHT 75G",
    454048: "GLOW&LOVELY FW GEL HYDRA 75G",
    407263: "ICHITAN THAI M.TEA PET 300ML",
    418146: "ICHITAN THAI G.TEA PET 300ML",
    413446: "ICHITAN THAI COFFE PET 300ML",
    440529: "ICHITAN THAI SALTCRML PET 300ML",
    450856: "ICHITAN MILKTEA CHEESE PET300ML",
    425653: "ICHITAN BROWN SGR PET 300ML",
    452793: "ICHITAN MILK MELON PET 300ML",
    119887: "PANTENE SHP HLS&LMBT 145/160ML",
    119895: "PANTENE SHP A.KETOMBE 145/160ML",
    119898: "PANTENE SHP RMBT RNTK 145/160ML",
    119899: "PANTENE SHP HTM GLOW 145/160ML",
    415150: "PANTENE SHP HJ A.KTMB 145/160ML",
    415376: "PANTENE SHP HJ A.RNTK 145/160ML",
    122157: "PANTENE COND RAMBUT RNTK 160ML",
    144353: "PANTENE COND HALUS&LEMBUT 160ML",
    428675: "PANTENE COND BIOTIN STRENGT70ML",
    428676: "PANTENE COND COLLGEN REPAIR70ML",
    431566: "PANTENE COND KERATIN GLOW 70ML",
    428817: "PANTENE COND MRC BIOTIN 150ML",
    428818: "PANTENE COND MRC COLLAGEN 150ML",
    453458: "PANTENE SHP MRCL COLLAGEN 145ML",
    453459: "PANTENE SHP MRCL BIOTIN 145ML",

    # ============================================================
    # GRUP 37: PLU SUGER (Tebus Murah)
    # ============================================================
    120333: "PUCUK HARUM TEH PET 350ML",
    407443: "SOSRO TEH BOTOL TAWAR PET 350ML",
    125338: "ICHI OCHA GREEN TEA PET 350ML",
    444255: "ULTRA TEH KOTAK LECI TP 300ML",
    444254: "ULTRA TEH KOTAK MANGGA TP 300ML",
    410515: "ULTRA TEH KOTAK LEMON TP 300ML",
    414351: "KUN UHT CHOMALT TPK 100ML",
}
# ============================================================
# FUNGSI BANTU
# ============================================================
def get_nama_plu(plu):
    """
    Cari nama PLU dengan auto-normalisasi.
    Coba:
      1. PLU asli (misal 4279272)
      2. Buang 1 digit terakhir (misal 427927)
      3. Buang 2 digit terakhir (misal 42792)
    """
    if plu is None:
        return "-"

    try:
        plu_int = int(float(plu))
    except (ValueError, TypeError):
        return "-"

    # Coba PLU asli
    if plu_int in PLU_NAMES:
        return PLU_NAMES[plu_int]

    # Coba buang 1 digit terakhir
    plu_str = str(plu_int)
    if len(plu_str) > 1:
        try:
            plu_min1 = int(plu_str[:-1])
            if plu_min1 in PLU_NAMES:
                return PLU_NAMES[plu_min1]
        except ValueError:
            pass

    # Coba buang 2 digit terakhir
    if len(plu_str) > 2:
        try:
            plu_min2 = int(plu_str[:-2])
            if plu_min2 in PLU_NAMES:
                return PLU_NAMES[plu_min2]
        except ValueError:
            pass

    return "-"


def get_plu_normalized(plu):
    """
    Return PLU yang sudah dinormalisasi (buang akhiran sampai match dict).
    Kalau tidak match, return PLU asli.
    """
    if plu is None:
        return None

    try:
        plu_int = int(float(plu))
    except (ValueError, TypeError):
        return None

    if plu_int in PLU_NAMES:
        return plu_int

    plu_str = str(plu_int)
    if len(plu_str) > 1:
        try:
            plu_min1 = int(plu_str[:-1])
            if plu_min1 in PLU_NAMES:
                return plu_min1
        except ValueError:
            pass

    if len(plu_str) > 2:
        try:
            plu_min2 = int(plu_str[:-2])
            if plu_min2 in PLU_NAMES:
                return plu_min2
        except ValueError:
            pass

    return plu_int


def get_nama_batch(plu_series):
    """
    Versi batch: terima pandas Series, return pandas Series nama.
    Lebih cepat dari loop satu-satu.
    """
    import pandas as pd
    return plu_series.apply(get_nama_plu)


# ============================================================
# STATISTIK (jalankan langsung: python plu_dict.py)
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("PLU DICTIONARY - STATISTIK")
    print("=" * 50)
    print("Total PLU di dictionary: " + str(len(PLU_NAMES)))
    print("")
    print("Contoh test auto-normalisasi:")
    print("  get_nama_plu(4279272) = " + get_nama_plu(4279272))
    print("  get_nama_plu(427927)  = " + get_nama_plu(427927))
    print("  get_nama_plu(4447552) = " + get_nama_plu(4447552))
    print("  get_nama_plu(444755)  = " + get_nama_plu(444755))
    print("  get_nama_plu(58682)   = " + get_nama_plu(58682))
    print("  get_nama_plu(5868)    = " + get_nama_plu(5868))
    print("  get_nama_plu(9999999) = " + get_nama_plu(9999999))
    print("")
    print("Contoh PLU normalized:")
    print("  get_plu_normalized(4279272) = " + str(get_plu_normalized(4279272)))
    print("  get_plu_normalized(427927)  = " + str(get_plu_normalized(427927)))
    print("  get_plu_normalized(4447552) = " + str(get_plu_normalized(4447552)))
