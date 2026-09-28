"""
Generates the synthetic case diary used by the demo.

Everything here is fictional: people, case numbers and events are invented.
Court names, statutes and procedure follow real Hyderabad / Telangana practice
so the data reads like an actual advocate's diary.

Dates are written relative to ANCHOR (the demo's "tomorrow"). At runtime the
app shifts every date so the anchor lands on the real tomorrow.

    python scripts/generate_data.py      -> data/diary.json
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

ANCHOR = date(2026, 9, 29)
OUT = Path(__file__).resolve().parent.parent / "data" / "diary.json"
rng = random.Random(1947)


def d(days_before_anchor: int) -> str:
    return (ANCHOR - timedelta(days=days_before_anchor)).isoformat()


def fmt_inr(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])


# --------------------------------------------------------------------------
# People and places
# --------------------------------------------------------------------------

ADVOCATE = {
    "name": "Adv. Ananya Rao",
    "chambers": "Chamber 14, Advocates' Block, Nampally Criminal Courts, Hyderabad",
    "enrolment": "TS/1184/2013",
}

COURTS = {
    "nampally-cmm14": "Court of the XIV Additional Chief Metropolitan Magistrate, Nampally, Hyderabad",
    "nampally-msj": "Court of the Metropolitan Sessions Judge, Nampally, Hyderabad",
    "nampally-ni": "Court of the XVII Special Magistrate (NI Act Cases), Nampally, Hyderabad",
    "tshc": "High Court for the State of Telangana, Hyderabad",
    "ccc-hyd": "City Civil Court, Hyderabad",
    "rr-lbnagar": "Court of the Principal Junior Civil Judge, Ranga Reddy District at L.B. Nagar",
    "mact-hyd": "Motor Accidents Claims Tribunal-cum-Chief Judge, City Small Causes Court, Hyderabad",
    "cdrc-hyd": "District Consumer Disputes Redressal Commission-I, Hyderabad",
    "family-sec": "Family Court, Secunderabad",
    "acb-hyd": "Court of the Principal Special Judge for SPE & ACB Cases, Hyderabad",
    "labour-hyd": "Industrial Tribunal-cum-Labour Court-I, Hyderabad",
}

JUDGES = {
    "J-KVR": {
        "name": "Sri K. Venkateswara Rao",
        "designation": "XIV Additional Chief Metropolitan Magistrate",
        "court": "nampally-cmm14",
        "traits": ["short-submissions", "strict-adjournments", "originals"],
    },
    "J-GAN": {
        "name": "Smt. G. Anuradha",
        "designation": "XIV Additional Chief Metropolitan Magistrate (transferred)",
        "court": "nampally-cmm14",
        "traits": ["lenient-dates"],
    },
    "J-PSM": {
        "name": "Sri P. Srinivasa Murthy",
        "designation": "Metropolitan Sessions Judge",
        "court": "nampally-msj",
        "traits": ["originals", "strict-adjournments"],
    },
    "J-NLK": {
        "name": "Smt. N. Lalitha Kumari",
        "designation": "XVII Special Magistrate (NI Act)",
        "court": "nampally-ni",
        "traits": ["settlement", "strict-adjournments"],
    },
    "J-SRV": {
        "name": "Hon'ble Justice S. Raghunandan Varma",
        "designation": "Judge, High Court for the State of Telangana",
        "court": "tshc",
        "traits": ["parity-bail", "short-submissions"],
    },
    "J-AVP": {
        "name": "Hon'ble Justice A. Vasudha Prasad",
        "designation": "Judge, High Court for the State of Telangana",
        "court": "tshc",
        "traits": ["originals", "lenient-dates"],
    },
    "J-MHK": {
        "name": "Sri M. Harikrishna",
        "designation": "IX Additional Chief Judge, City Civil Court",
        "court": "ccc-hyd",
        "traits": ["settlement", "lenient-dates"],
    },
    "J-RSP": {
        "name": "Smt. R. Sai Prasanna",
        "designation": "Principal Junior Civil Judge",
        "court": "rr-lbnagar",
        "traits": ["originals", "strict-adjournments"],
    },
    "J-DVS": {
        "name": "Sri D. Vijaya Sarathi",
        "designation": "Chairman, Motor Accidents Claims Tribunal",
        "court": "mact-hyd",
        "traits": ["settlement", "short-submissions"],
    },
    "J-CKR": {
        "name": "Smt. Ch. Kalyani Reddy",
        "designation": "President, District Consumer Commission-I",
        "court": "cdrc-hyd",
        "traits": ["short-submissions", "settlement"],
    },
    "J-YSN": {
        "name": "Smt. Y. Sunitha",
        "designation": "Judge, Family Court",
        "court": "family-sec",
        "traits": ["settlement", "lenient-dates"],
    },
    "J-TBR": {
        "name": "Sri T. Bhaskar Reddy",
        "designation": "Principal Special Judge for SPE & ACB Cases",
        "court": "acb-hyd",
        "traits": ["originals", "strict-adjournments"],
    },
    "J-LNS": {
        "name": "Sri L. Narasimha Swamy",
        "designation": "Presiding Officer, Industrial Tribunal-cum-Labour Court-I",
        "court": "labour-hyd",
        "traits": ["lenient-dates", "settlement"],
    },
}

COUNSEL = {
    "C-BNC": {"name": "Sri B. Narasimha Chary", "role": "Assistant Public Prosecutor", "habit": "medical-adjournment"},
    "C-KSL": {"name": "Smt. K. Sulochana", "role": "Additional Public Prosecutor", "habit": "io-absent"},
    "C-MSG": {"name": "Sri M. Srikanth Goud", "role": "Advocate", "habit": "late-compilation"},
    "C-VPR": {"name": "Sri V. Pradeep Rao", "role": "Advocate", "habit": "maintainability"},
    "C-SAH": {"name": "Sri Syed Ahmed Hussain", "role": "Advocate", "habit": "settle-under-pressure"},
    "C-RJK": {"name": "Smt. R. Jhansi Kiran", "role": "Advocate", "habit": "cites-unsupplied"},
    "C-GVS": {"name": "Sri G. Venu Shekar", "role": "Standing Counsel, GHMC", "habit": "time-for-instructions"},
    "C-PLN": {"name": "Sri P. Lakshmi Narayana", "role": "Public Prosecutor (High Court)", "habit": "time-for-instructions"},
    "C-TKM": {"name": "Sri T. Kiran Mohan", "role": "Advocate for Insurer", "habit": "late-compilation"},
    "C-AFR": {"name": "Smt. Afreen Fatima", "role": "Advocate", "habit": "settle-under-pressure"},
    "C-NRS": {"name": "Sri N. Ravi Shankar", "role": "Special Public Prosecutor (ACB)", "habit": "io-absent"},
    "C-JVR": {"name": "Sri J. Vamshi Reddy", "role": "Advocate", "habit": "maintainability"},
}

HABIT_ADJ_REASONS = {
    "medical-adjournment": [
        ("medical", "counsel reported unwell and filed a memo seeking time"),
        ("medical", "counsel said he was advised bed rest after a viral fever"),
        ("medical", "counsel cited a scheduled medical procedure"),
    ],
    "io-absent": [
        ("witness", "the Investigating Officer was on bandobast duty and could not attend"),
        ("witness", "the IO had been transferred and summons were yet to be served afresh"),
    ],
    "late-compilation": [
        ("documents", "counsel sought time to file a compilation of judgments, served on us only in court"),
        ("documents", "counsel wanted time to file additional documents under Order VII Rule 14"),
    ],
    "maintainability": [
        ("objection", "counsel pressed a fresh maintainability objection and sought time to file a memo"),
    ],
    "settle-under-pressure": [
        ("settlement", "counsel sought time stating the parties were exploring settlement"),
    ],
    "cites-unsupplied": [
        ("documents", "counsel relied on judgments not supplied in advance and the court gave time for us to respond"),
    ],
    "time-for-instructions": [
        ("instructions", "counsel sought time to obtain instructions from the department"),
    ],
}

JUDGE_REMARKS = {
    "short-submissions": [
        "The court remarked that it will not read lengthy written notes and directed a synopsis not exceeding five pages.",
        "The judge cut short the reading of judgments and asked counsel to confine arguments to the two points actually in issue.",
        "The bench asked that written submissions be filed as a short note with page references, not a compilation.",
    ],
    "strict-adjournments": [
        "The court made it clear that no further adjournment would be granted without costs.",
        "The judge recorded that the matter is old and directed both sides to be ready without fail on the next date.",
        "The court observed that repeated adjournment requests will be viewed seriously and asked for an affidavit with any future request.",
    ],
    "originals": [
        "The court insisted on originals being produced for comparison and refused to act on photocopies.",
        "The judge asked for certified copies, not attested photocopies, before the exhibit could be marked.",
    ],
    "settlement": [
        "The court asked whether the parties had explored settlement and suggested referral to the Lok Adalat.",
        "The bench suggested mediation at the Legal Services Authority before taking up arguments.",
    ],
    "lenient-dates": [
        "The court granted a long date on the request of both sides.",
        "The court accommodated the request and noted that the matter would be taken up in the next cycle.",
    ],
    "parity-bail": [
        "The court asked whether co-accused had been enlarged on bail and on what terms, indicating parity would weigh.",
        "The bench asked for the period of custody undergone and the status of the charge sheet.",
    ],
}

CLIENTS = [
    "Mohammed Irfan Qureshi", "Bandaru Swapna", "Gadde Sai Kiran", "Nallamothu Harish", "Syeda Nikhat Parveen",
    "Kommineni Ravindra", "Pothuri Lakshmi Prasanna", "Arvind Kumar Agarwal", "Chinta Venkatesh", "Mallela Srinivas",
    "Deepika Reddy Challa", "Rajesh Jain", "Thota Nagaraju", "Kavitha Yerramsetti", "Sunil Kumar Bhandari",
    "Pendyala Madhavi", "Farhan Siddiqui", "Uppalapati Kiran Varma", "Jyothi Lakshmi Bolla", "Siva Prasad Gummadi",
    "Anil Goud Kasula", "Rama Devi Tadikonda", "Venkata Subbaiah Duggirala", "Neha Sharma Tripathi", "Abdul Kareem",
    "Srilatha Musunuri", "Prakash Rao Vadlamudi", "Harini Chowdary", "Yashwanth Reddy Mekala", "Shaik Mastan Vali",
    "Vijaya Kumari Pinnamaneni", "Naveen Chandra Akula", "Madhusudhan Rao Katta", "Sowmya Iyer", "Ramesh Babu Kolli",
    "Anjali Deshpande", "Gopi Krishna Nandyala", "Rukhsana Begum", "Satyanarayana Murthy Veeramachaneni",
    "Pallavi Joshi", "Chandrasekhar Pasupuleti", "Mounika Vemula", "Ajay Singh Thakur", "Lalitha Ramanujam",
    "Karthik Surapaneni", "Zoya Mirza", "Nagendra Babu Tallapaka", "Bhavani Shankar Oruganti",
]

OPPONENTS = [
    "Sri Sai Balaji Constructions Pvt. Ltd.", "Vasavi Traders", "Greenfield Agro Industries", "Sravani Infra Projects LLP",
    "ICICI Lombard General Insurance Co. Ltd.", "The New India Assurance Co. Ltd.", "Bajaj Allianz General Insurance Co. Ltd.",
    "Greater Hyderabad Municipal Corporation", "Hyderabad Metropolitan Development Authority", "Sri Venkateshwara Chit Funds",
    "Karthikeya Automobiles (Maruti Suzuki Arena, Kukatpally)", "Sri Lakshmi Ganapathi Electronics", "Deccan Logistics Pvt. Ltd.",
    "Telangana State Southern Power Distribution Co. Ltd.", "Aditya Hi-Tech Solutions", "Vijetha Supermarkets",
]

BANKS = ["HDFC Bank", "State Bank of India", "ICICI Bank", "Axis Bank", "Union Bank of India", "Canara Bank",
         "Karur Vysya Bank", "The A.P. Mahesh Co-operative Urban Bank"]
BRANCHES = ["Kukatpally", "Ameerpet", "Dilsukhnagar", "Madhapur", "Abids", "Secunderabad", "Kondapur", "Miyapur",
            "L.B. Nagar", "Himayatnagar", "Mehdipatnam", "Begumpet"]
VILLAGES = ["Bachupally", "Gajularamaram", "Nizampet", "Kompally", "Shamshabad", "Peerzadiguda", "Adibatla",
            "Kismatpur", "Bandlaguda Jagir", "Pragathi Nagar", "Medchal", "Tukkuguda"]

PRODUCTS = [
    ("Daikin 1.5 Ton 5 Star Inverter Split AC, model FTKF50TV16U", 52990),
    ("Samsung 8 kg Front Load Washing Machine, model WW80T504DAW", 38490),
    ("LG 655 L Side-by-Side Refrigerator, model GL-B257HDSY", 84990),
    ("Apple iPhone 14, 128 GB (model A2882)", 69900),
    ("Kent Grand Plus RO Water Purifier, model 11007", 18500),
    ("Voltas 1.5 Ton 3 Star Window AC, model 183 LZH", 31990),
    ("Hero Splendor Plus XTEC (BS-VI), engine no. HA11EVP4G21873", 79911),
    ("Maruti Suzuki Brezza VXi (AT), chassis MA3NYFB1SPK418823", 1238000),
    ("Dell Inspiron 15 3520 laptop, service tag 7XQ2KN3", 58990),
    ("Havells Adonia 25 L water heater, model GHWAAQTWH025", 21999),
]

VEHICLES = [
    ("TS 09 EX 4417", "Tata Ace Gold goods carrier"),
    ("TS 08 UB 2291", "Ashok Leyland Dost+ LCV"),
    ("TS 07 GN 9834", "Royal Enfield Classic 350"),
    ("AP 28 TC 6612", "TSRTC Palle Velugu bus (Tata LP 909)"),
    ("TS 13 EQ 0718", "Hyundai Creta SX"),
    ("TS 10 FA 5530", "Bajaj RE Compact auto-rickshaw"),
    ("TS 15 UC 3307", "Eicher Pro 2049 truck"),
]


# --------------------------------------------------------------------------
# Hand-written flagship case: Reddy vs. State of Telangana
# --------------------------------------------------------------------------

def reddy_case():
    cid = "reddy-vs-state"
    case = {
        "id": cid,
        "title": "Reddy vs. State of Telangana",
        "short": "Reddy",
        "case_no": "C.C. No. 1187 of 2023",
        "cnr": "TSHY010118712023",
        "crime": "Cr. No. 218/2022, CCS Hyderabad",
        "court": "nampally-cmm14",
        "judge": "J-KVR",
        "type": "Criminal trial",
        "subject": "Sections 420, 406 r/w 120-B IPC — alleged cheating in sale of a flat at Sri Sai Residency, Bachupally",
        "client": {"name": "Kasireddy Venkata Ramana Reddy", "role": "Accused No. 1", "phone": "+91 98480 21736"},
        "opponent": "State of Telangana, rep. by CCS Hyderabad (de facto complainant: Smt. Padmaja Gorantla)",
        "opp_counsel": "C-BNC",
        "other_counsel": ["C-MSG"],
        "value": 4200000,
        "filed": d(1300),
        "status": "Trial — prosecution evidence",
        "summary": ("Complainant alleges she paid for Flat 402, Block B, Sri Sai Residency, Bachupally under an agreement "
                    "dated 14 Feb 2021 and the flat was never delivered. Our client's defence: the payment was part of "
                    "a joint-venture dispute with the landowner, and the flat was ready for registration in 2022."),
    }

    H = []

    def hearing(no, days, judge, stage, notes, **kw):
        h = {
            "id": f"RDY-H{no:02d}", "case_id": cid, "no": no, "date": d(days), "judge": judge,
            "counsel": "C-BNC", "stage": stage, "notes": notes,
            "asked": kw.get("asked", []), "adjournment": kw.get("adj"), "opp_args": kw.get("opp", []),
            "our_args": kw.get("ours", []), "due": kw.get("due", []), "promises": kw.get("promises", []),
            "outcome": kw.get("outcome", ""), "lesson": kw.get("lesson", ""),
        }
        H.append(h)

    hearing(1, 1240, "J-GAN", "Appearance of accused",
            "Client appeared on summons with sureties. Bail bonds of ₹25,000 with two sureties accepted. Copies of the "
            "charge sheet (38 pages) and documents furnished under Section 207 CrPC.",
            outcome="Accused enlarged on bail; case posted for framing of charges.",
            promises=["Explained to client that personal attendance is required on every date unless exempted."])
    hearing(2, 1170, "J-GAN", "Framing of charges",
            "Charges framed under Sections 420 and 406 r/w 120-B IPC. Accused pleaded not guilty and claimed trial. "
            "Charge records the alleged amount paid as ₹42,00,000.",
            ours=["Opposed framing of Section 406 as the amount was paid under an agreement of sale, not entrusted."],
            outcome="Charges framed; trial to commence with PW-1.")
    hearing(3, 1090, "J-GAN", "Prosecution evidence — documents",
            "Prosecution filed list of witnesses (11) and documents. Court directed the prosecution to produce a certified "
            "copy of the HDFC Bank statement for account ending 4471 (Kukatpally branch) for Feb–Jun 2021, as the "
            "photocopy on record is unattested.",
            asked=["Certified copy of HDFC Bank statement, A/c ending 4471, Feb–Jun 2021 (prosecution to produce)."],
            due=[{"item": "Certified HDFC Bank statement, A/c ending 4471", "by": "prosecution", "status": "pending"}],
            outcome="Posted for PW-1 chief examination.")
    hearing(4, 1020, "J-GAN", "PW-1 chief examination",
            "PW-1 (complainant Smt. Padmaja Gorantla) was present but the prosecution was not ready with the document "
            "file. Complainant's counsel Sri M. Srikanth Goud handed us a 212-page compilation in court.",
            adj={"by": "opposing", "counsel": "C-BNC", "ground": "documents",
                 "reason": "APP stated the case diary had not been received from CCS"},
            outcome="Adjourned at the request of the prosecution.")
    hearing(5, 950, "J-GAN", "PW-1 chief examination",
            "APP Sri B. Narasimha Chary was absent; a memo was filed stating he was unwell. Complainant present.",
            adj={"by": "opposing", "counsel": "C-BNC", "ground": "medical",
                 "reason": "APP filed a memo stating he was unwell with fever"},
            outcome="Adjourned; court noted the complainant's attendance.",
            promises=["Promised client we would press for a shorter date so his travel from Kondapur is not wasted."])
    hearing(6, 880, "J-KVR", "PW-1 chief examination",
            "New presiding officer Sri K. Venkateswara Rao took charge after the transfer of Smt. G. Anuradha. PW-1 "
            "examined in chief in part. Exhibits P-1 (agreement of sale dated 14.02.2021, photocopy) and P-2 (receipts) "
            "marked subject to objection.",
            ours=["Objected to marking a photocopy of the agreement of sale; original is said to be with the complainant."],
            asked=["Complainant to produce the original agreement of sale dated 14.02.2021 at the time of cross."],
            due=[{"item": "Original agreement of sale dated 14.02.2021", "by": "complainant", "status": "pending"}],
            outcome="Chief examination of PW-1 to continue.")
    hearing(7, 810, "J-KVR", "PW-1 chief examination (continued)",
            "PW-1 completed chief. In chief she stated she paid ₹38,50,000 towards the flat and that ₹3,50,000 was a "
            "separate payment for registration charges which was later refunded to her. This differs from the charge, "
            "which records ₹42,00,000 as the amount cheated.",
            ours=["Noted the discrepancy between ₹42,00,000 in the charge and ₹38,50,000 in PW-1's chief for use in cross."],
            outcome="Posted for cross-examination of PW-1.",
            lesson="The amount discrepancy is the strongest point for cross; do not reveal it before PW-1 is in the box.")
    hearing(8, 740, "J-KVR", "Cross-examination of PW-1",
            "PW-1 cross-examined for about two hours. Prosecution sought to mark WhatsApp chats retrieved from the "
            "complainant's Samsung Galaxy S21 FE (model SM-G990E). We objected: no certificate under Section 65B of the "
            "Evidence Act has been filed.",
            ours=["Section 65B(4) certificate is mandatory for secondary electronic evidence (Arjun Panditrao Khotkar)."],
            asked=["Prosecution to file the Section 65B certificate for the WhatsApp chat printouts before they are marked."],
            due=[{"item": "Section 65B certificate for WhatsApp chats (Samsung SM-G990E)", "by": "prosecution", "status": "pending"}],
            promises=["Promised client a written update on whether the WhatsApp chats will be admitted."],
            outcome="Chats not marked; cross of PW-1 to conclude next date.")
    hearing(9, 670, "J-KVR", "Cross-examination of PW-1 (concluded)",
            "Cross of PW-1 concluded. She admitted the ₹3,50,000 was refunded by cheque in Aug 2021. Prosecution produced "
            "only a partial HDFC statement (Feb–Mar 2021) — certified, but Apr–Jun 2021 is still missing. Client raised "
            "that his passport, seized during investigation, is needed for his daughter's wedding in Dubai.",
            due=[{"item": "Certified HDFC Bank statement, Apr–Jun 2021 portion", "by": "prosecution", "status": "partial"}],
            promises=["Promised client we would file a petition for return of the seized passport (Crl.M.P.) before the wedding in November."],
            outcome="PW-1 discharged. PW-2 (site engineer) summoned.")
    hearing(10, 600, "J-KVR", "PW-2 examination",
            "PW-2 Sri Ch. Mahesh (site engineer) examined and cross-examined; he admitted Block B had received the "
            "occupancy certificate in Oct 2022. Prosecution filed a Section 65B certificate for the chats, but it is "
            "signed by the Investigating Officer, not by the person in charge of the device.",
            ours=["Objected to the certificate: signed by the IO, who was never in lawful control of the phone."],
            due=[{"item": "Our objection to defective Section 65B certificate", "by": "court", "status": "pending"}],
            outcome="Objection to certificate reserved; to be decided at the time of final arguments.",
            lesson="PW-2's admission on the occupancy certificate supports the 'flat was ready' defence.")
    hearing(11, 520, "J-KVR", "PW-3 examination",
            "PW-3 Sri Sandeep Kulkarni (Branch Manager, HDFC Bank, Kukatpally) was present with records, but the "
            "prosecution sought time because the Investigating Officer was on election duty.",
            adj={"by": "opposing", "counsel": "C-BNC", "ground": "witness",
                 "reason": "APP said the IO was on election bandobast duty"},
            asked=["Court directed that PW-3 be bound over for the next date."],
            outcome="Adjourned at the instance of the prosecution; PW-3 bound over.")
    hearing(12, 430, "J-KVR", "PW-3 examination",
            "PW-3 examined in chief. Complainant's counsel tried to file 44 pages of written notes. The judge refused and "
            "said the court will not read long notes; any submission must be a synopsis of not more than five pages.",
            asked=["Any written submission to be a synopsis of five pages or less."],
            promises=["Told client the passport petition is drafted and will be filed after the certified bank statement issue is settled."],
            outcome="PW-3 chief completed; cross deferred at defence request to obtain bank ledger.",
            lesson="This judge rejects long written notes outright. Keep our synopsis to five pages with exhibit references.")
    hearing(13, 330, "J-KVR", "Cross-examination of PW-3",
            "APP Chary again filed a medical memo. The judge was visibly displeased and recorded that this is the third "
            "adjournment sought by the prosecution in this case. He imposed costs of ₹2,000 and said any future request "
            "must be supported by an affidavit and medical certificate.",
            adj={"by": "opposing", "counsel": "C-BNC", "ground": "medical",
                 "reason": "APP filed a memo citing a scheduled medical procedure"},
            asked=["Future adjournment requests only on affidavit with medical certificate; costs ₹2,000 imposed on prosecution."],
            outcome="Adjourned with costs of ₹2,000 payable to the Legal Services Authority.",
            lesson="The judge is now keeping count of prosecution adjournments. Point to his own order if it happens again.")
    hearing(14, 70, "J-KVR", "Cross-examination of PW-3",
            "PW-3 cross-examined in part. He confirmed that the Apr–Jun 2021 statement exists in the bank's archive and "
            "could be certified within a week of a request. The judge said this is the last opportunity for the "
            "prosecution to produce the full certified statement; otherwise the court will proceed on the record as it "
            "stands. He also asked the defence to state clearly whether we dispute the signature on Ex. P-4 (receipt dated 02.03.2021).",
            asked=["Prosecution: last chance to produce full certified HDFC statement (Apr–Jun 2021).",
                   "Defence: state whether we dispute the signature on Ex. P-4 (receipt dated 02.03.2021).",
                   "Complainant: produce the original agreement of sale dated 14.02.2021."],
            due=[{"item": "Certified HDFC Bank statement, Apr–Jun 2021 portion", "by": "prosecution", "status": "pending"},
                 {"item": "Original agreement of sale dated 14.02.2021", "by": "complainant", "status": "pending"},
                 {"item": "Defence stand on signature in Ex. P-4", "by": "us", "status": "pending"}],
            promises=["Promised client an update on the passport petition before the next date.",
                      "Promised client we would get certified copies of PW-1 and PW-3 depositions."],
            outcome="Remaining cross of PW-3 deferred to the next date.")

    case["next_date"] = d(0)
    case["next_purpose"] = "Cross-examination of PW-3 (continued); production of certified bank statement"
    return case, H


# --------------------------------------------------------------------------
# Hand-written pattern cases: APP Chary before Sri K. Venkateswara Rao
# --------------------------------------------------------------------------

def chary_pattern_cases():
    specs = [
        ("state-vs-imran", "State vs. Syed Imran", "C.C. No. 2231 of 2024", "Syed Imran",
         "Sections 379, 411 IPC — theft of a Hero Splendor Plus (TS 07 GN 1128)", 180,
         [("medical", "APP Chary filed a medical memo stating he was down with dengue."),
          (None, "PW-2 examined. Nothing turned on it."),
          ("medical", "APP Chary sought time citing physiotherapy after a back injury. Court granted time but warned the prosecution.")]),
        ("state-vs-lavanya", "State vs. Lavanya Kotha", "C.C. No. 988 of 2024", "Lavanya Kotha",
         "Section 138 read with 142 NI Act transferred for trial — cheque for ₹6,40,000 (Canara Bank, Ameerpet)", 120,
         [(None, "Complainant's evidence on affidavit received."),
          ("witness", "APP Chary sought time as the investigating officer did not turn up with the case property.")]),
        ("state-vs-raghavendra", "State vs. P. Raghavendra", "C.C. No. 1502 of 2023", "P. Raghavendra",
         "Section 304-A IPC — road accident involving Eicher Pro 2049 truck (TS 15 UC 3307)", 95,
         [(None, "APP Chary was ready; PW-4 and PW-5 examined and discharged the same day."),
          (None, "Section 313 CrPC examination completed.")]),
        ("state-vs-afzal", "State vs. Mohd. Afzal", "C.C. No. 310 of 2025", "Mohd. Afzal",
         "Section 406 IPC — alleged misappropriation of ₹11,75,000 by a supervisor at Deccan Logistics", 40,
         [(None, "Charges framed."),
          ("medical", "APP Chary sought an adjournment stating he had a medical appointment. The judge recorded it and "
                      "said the next request would need a medical certificate.")]),
    ]
    cases, hearings = [], []
    for cid, title, cno, client, subject, last_days, events in specs:
        case = {
            "id": cid, "title": title, "short": title.split("vs. ")[-1].split()[-1], "case_no": cno,
            "cnr": f"TSHY01{rng.randint(1000, 9999):04d}{rng.randint(10, 99)}20{cno[-2:]}",
            "court": "nampally-cmm14", "judge": "J-KVR", "type": "Criminal trial", "subject": subject,
            "client": {"name": client, "role": "Accused", "phone": f"+91 9{rng.randint(100000000, 999999999)}"},
            "opponent": "State of Telangana", "opp_counsel": "C-BNC", "other_counsel": [],
            "value": 0, "filed": d(last_days + 60 * len(events) + 200), "status": "Trial — prosecution evidence",
            "summary": subject + ".",
        }
        if cid == "state-vs-raghavendra":
            case["status"] = "Arguments"
        for i, (ground, note) in enumerate(events, start=1):
            days = last_days + (len(events) - i) * rng.randint(45, 70)
            adj = None
            if ground:
                adj = {"by": "opposing", "counsel": "C-BNC", "ground": ground, "reason": note}
            asked = []
            if ground == "medical" and i == len(events):
                asked = ["Any future adjournment request by the prosecution must be supported by a medical certificate."]
            hearings.append({
                "id": f"{cid[:10].upper()}-H{i:02d}", "case_id": cid, "no": i, "date": d(days), "judge": "J-KVR",
                "counsel": "C-BNC", "stage": "Prosecution evidence", "notes": note, "asked": asked, "adjournment": adj,
                "opp_args": [], "our_args": [], "due": [], "promises": [],
                "outcome": "Adjourned at the request of the prosecution." if adj else "Proceeded as listed.",
                "lesson": "",
            })
        case["next_date"] = d(-rng.randint(6, 40))
        case["next_purpose"] = "Prosecution evidence"
        cases.append(case)
    return cases, hearings


# --------------------------------------------------------------------------
# Bail matters before the High Court: a pattern of what worked
# --------------------------------------------------------------------------

def bail_cases():
    specs = [
        ("bail-naresh", "Kolli Naresh vs. State of Telangana", "Crl.P. No. 8812 of 2025", "Kolli Naresh",
         "Regular bail — Sections 420, 468 IPC, custody 94 days", "J-SRV", True,
         "Argued parity with co-accused A2 who was bailed in Crl.P. 7710/2025, plus 94 days in custody and charge sheet filed.",
         "Bail granted on parity, with conditions to appear before the SHO every Monday; personal bond of ₹50,000."),
        ("bail-shafi", "Mohd. Shafi vs. State of Telangana", "Crl.P. No. 2217 of 2026", "Mohd. Shafi",
         "Regular bail — Sections 8(c) r/w 20(b)(ii)(B) NDPS Act, 1.2 kg ganja", "J-SRV", True,
         "Argued intermediate quantity, custody of 5 months, and that co-accused had been released; kept submissions to 10 minutes.",
         "Bail granted; the judge noted counsel's brevity and the parity point."),
        ("bail-deepak", "Deepak Soni vs. State of Telangana", "Crl.P. No. 5530 of 2025", "Deepak Soni",
         "Anticipatory bail — Section 406 IPC, business dispute of ₹27,40,000", "J-SRV", False,
         "Read out three Supreme Court judgments at length on the civil nature of the dispute; did not address parity.",
         "Petition dismissed; the judge said the petitioner may approach the trial court after appearance."),
        ("bail-venkat", "B. Venkatesh vs. State of Telangana", "Crl.P. No. 1904 of 2026", "Bandi Venkatesh",
         "Regular bail — Sections 302 r/w 34 IPC, custody 11 months", "J-AVP", False,
         "Argued long custody. The State opposed citing a threat to witnesses; originals of the witness complaint were produced.",
         "Bail rejected with liberty to renew after the eyewitnesses are examined."),
    ]
    cases, hearings = [], []
    for cid, title, cno, client, subject, judge, granted, argued, result in specs:
        case = {
            "id": cid, "title": title, "short": client.split()[-1], "case_no": cno,
            "cnr": f"TSHC01{rng.randint(100000, 999999)}20{cno[-2:]}", "court": "tshc", "judge": judge,
            "type": "Bail", "subject": subject,
            "client": {"name": client, "role": "Petitioner / Accused", "phone": f"+91 9{rng.randint(100000000, 999999999)}"},
            "opponent": "State of Telangana, rep. by Public Prosecutor", "opp_counsel": "C-PLN", "other_counsel": [],
            "value": 0, "filed": d(rng.randint(140, 400)), "status": "Disposed", "summary": subject + ".",
            "next_date": None, "next_purpose": None,
        }
        base = rng.randint(60, 300)
        hearings.append({
            "id": f"{cid.upper()}-H01", "case_id": cid, "no": 1, "date": d(base + 21), "judge": judge, "counsel": "C-PLN",
            "stage": "Admission", "notes": "Notice issued to the Public Prosecutor. PP sought time for instructions and the case diary.",
            "asked": ["PP to obtain instructions and produce the case diary."],
            "adjournment": {"by": "opposing", "counsel": "C-PLN", "ground": "instructions", "reason": "PP sought time for instructions"},
            "opp_args": [], "our_args": [], "due": [], "promises": [], "outcome": "Notice; posted in two weeks.", "lesson": "",
        })
        hearings.append({
            "id": f"{cid.upper()}-H02", "case_id": cid, "no": 2, "date": d(base), "judge": judge, "counsel": "C-PLN",
            "stage": "Hearing", "notes": argued,
            "asked": [JUDGE_REMARKS["parity-bail"][0]] if judge == "J-SRV" else [],
            "adjournment": None, "opp_args": ["PP opposed on the ground of the gravity of the offence."],
            "our_args": [argued], "due": [], "promises": [], "outcome": result,
            "lesson": ("Before Justice Varma, lead with parity and custody period and keep it short." if granted and judge == "J-SRV"
                       else "Long readings of judgments did not help before Justice Varma." if judge == "J-SRV" else ""),
        })
        cases.append(case)
    return cases, hearings


# --------------------------------------------------------------------------
# Templated practice: the rest of the docket
# --------------------------------------------------------------------------

def gen_ni_act(i, client):
    amt = rng.choice([245000, 480000, 675000, 920000, 1250000, 1875000, 2640000, 4800000])
    bank, branch = rng.choice(BANKS), rng.choice(BRANCHES)
    chq = rng.randint(100000, 999999)
    opp = rng.choice(OPPONENTS[:4] + OPPONENTS[9:13])
    return {
        "title": f"{client} vs. {opp.split(' (')[0]}", "court": "nampally-ni", "judge": "J-NLK",
        "type": "Cheque bounce (NI Act)", "value": amt,
        "subject": f"Section 138 NI Act — cheque no. {chq} for {fmt_inr(amt)} drawn on {bank}, {branch}, returned 'funds insufficient'",
        "opponent": opp, "role": "Complainant", "case_no": f"C.C. No. {rng.randint(1200, 9800)} of {rng.choice([2022, 2023, 2024])}",
        "stages": ["Appearance of accused", "Plea of accused", "Complainant's evidence on affidavit",
                   "Cross-examination of complainant", "Section 313 examination", "Defence evidence", "Arguments"],
        "facts": [f"Legal notice dated within 30 days of the return memo was served; the accused did not pay {fmt_inr(amt)}."],
        "docs": [f"Return memo from {bank}, {branch}", "Original dishonoured cheque", "Postal acknowledgment of legal notice",
                 "Certified copy of the partnership deed"],
    }


def gen_civil(i, client):
    village = rng.choice(VILLAGES)
    sy = f"{rng.randint(12, 480)}/{rng.choice(['A', 'AA', '1', '2', 'E'])}"
    val = rng.choice([1850000, 3200000, 5600000, 8400000, 12500000])
    kind = rng.choice(["injunction", "recovery", "partition"])
    court, judge = rng.choice([("ccc-hyd", "J-MHK"), ("rr-lbnagar", "J-RSP")])
    opp = rng.choice(OPPONENTS[:4] + ["Kasula Yadagiri", "Bollam Anjaiah and 3 others", "Mekala Sudhakar Reddy"])
    subj = {
        "injunction": f"Suit for perpetual injunction over open plot in Sy. No. {sy}, {village} (approx. 300 sq. yds.)",
        "recovery": f"Suit for recovery of {fmt_inr(val)} with interest at 18% p.a. under a promissory note",
        "partition": f"Suit for partition of ancestral agricultural land, Sy. No. {sy}, {village} (Ac. 4.20 gts.)",
    }[kind]
    return {
        "title": f"{client} vs. {opp}", "court": court, "judge": judge, "type": "Civil suit", "value": val,
        "subject": subj, "opponent": opp, "role": "Plaintiff",
        "case_no": f"O.S. No. {rng.randint(100, 2400)} of {rng.choice([2019, 2020, 2021, 2022, 2023])}",
        "stages": ["Written statement", "Settlement of issues", "Plaintiff's evidence (PW-1 chief affidavit)",
                   "Cross-examination of PW-1", "Defendant's evidence", "Arguments"],
        "facts": [f"The encumbrance certificate for Sy. No. {sy} shows no prior transaction." if kind != "recovery"
                  else "The promissory note is on a ₹100 non-judicial stamp paper."],
        "docs": ["Certified copy of the sale deed", f"Pahani / ROR-1B for Sy. No. {sy}", "Encumbrance certificate (30 years)",
                 "Advocate Commissioner's report", "Original promissory note"],
    }


def gen_mact(i, client):
    reg, veh = rng.choice(VEHICLES)
    comp = rng.choice([850000, 1500000, 2400000, 3500000, 5000000])
    insurer = rng.choice(OPPONENTS[4:7])
    return {
        "title": f"{client} vs. {insurer.split(' Co.')[0]} and another", "court": "mact-hyd", "judge": "J-DVS",
        "type": "Motor accident claim", "value": comp,
        "subject": f"Claim for {fmt_inr(comp)} compensation — accident involving {veh} ({reg}) on the Outer Ring Road near Gachibowli",
        "opponent": insurer, "role": "Claimant", "case_no": f"M.V.O.P. No. {rng.randint(300, 2900)} of {rng.choice([2022, 2023, 2024])}",
        "stages": ["Counter of insurer", "Claimant's evidence", "Cross by insurer", "Doctor's evidence (disability)",
                   "Insurer's evidence", "Arguments"],
        "facts": [f"FIR registered at Gachibowli PS; the driver of {reg} held a valid licence per the RTA extract."],
        "docs": ["Certified copy of FIR and charge sheet", "Wound certificate and disability certificate",
                 "Salary certificate / ITR for three years", f"RC and insurance policy of {reg}"],
    }


def gen_consumer(i, client):
    prod, price = rng.choice(PRODUCTS)
    opp = rng.choice(["Sri Lakshmi Ganapathi Electronics", "Karthikeya Automobiles (Maruti Suzuki Arena, Kukatpally)",
                      "Aditya Hi-Tech Solutions", "Vijetha Supermarkets"])
    return {
        "title": f"{client} vs. {opp.split(' (')[0]} and another", "court": "cdrc-hyd", "judge": "J-CKR",
        "type": "Consumer complaint", "value": price,
        "subject": f"Deficiency in service — {prod}, bought for {fmt_inr(price)}, repeated failure within warranty",
        "opponent": opp, "role": "Complainant", "case_no": f"C.C. No. {rng.randint(100, 900)} of {rng.choice([2024, 2025])}",
        "stages": ["Version of opposite parties", "Evidence affidavit of complainant", "Evidence of opposite parties",
                   "Written arguments", "Oral arguments"],
        "facts": [f"Three service job cards were raised for the {prod.split(',')[0]} within 11 months."],
        "docs": ["Tax invoice", "Warranty card", "Service job cards", "Email correspondence with the manufacturer"],
    }


def gen_family(i, client):
    amt = rng.choice([8000, 12000, 15000, 20000, 25000, 35000])
    return {
        "title": f"{client} vs. {rng.choice(['Ch. Srikanth', 'K. Mahender', 'P. Sravan Kumar', 'Imran Baig'])}",
        "court": "family-sec", "judge": "J-YSN", "type": "Family (maintenance)", "value": amt * 12,
        "subject": f"Maintenance under Section 125 CrPC — claim of {fmt_inr(amt)} per month for wife and minor child",
        "opponent": "Respondent husband", "role": "Petitioner",
        "case_no": f"M.C. No. {rng.randint(40, 700)} of {rng.choice([2023, 2024, 2025])}",
        "stages": ["Counter", "Counselling", "Petitioner's evidence", "Respondent's evidence", "Arguments"],
        "facts": [f"Respondent's salary slip shows net pay of {fmt_inr(amt * 5 + rng.randint(1000, 9000))} per month."],
        "docs": ["Marriage certificate", "Child's birth certificate", "Respondent's salary slips (Form 16)",
                 "Affidavit of assets and liabilities (Rajnesh v. Neha format)"],
    }


def gen_writ(i, client):
    return {
        "title": f"{client} vs. State of Telangana and others", "court": "tshc", "judge": "J-AVP",
        "type": "Writ petition", "value": 0,
        "subject": "Challenge to GHMC demolition notice under Section 461 GHMC Act for a G+2 building at "
                   f"{rng.choice(['Tolichowki', 'Chintal', 'Moosapet', 'Saroornagar'])}",
        "opponent": "Greater Hyderabad Municipal Corporation", "role": "Petitioner",
        "case_no": f"W.P. No. {rng.randint(1000, 29000)} of {rng.choice([2024, 2025])}",
        "stages": ["Admission", "Interim orders", "Counter affidavit", "Reply affidavit", "Final hearing"],
        "facts": ["The building permission (File No. 2/C19/10254/2019) covers G+1; the third floor is disputed."],
        "docs": ["Building permission and approved plan", "Demolition notice", "Property tax receipts", "Photographs of the site"],
    }


def gen_acb(i, client):
    amt = rng.choice([15000, 25000, 40000, 75000])
    return {
        "title": f"State (ACB) vs. {client}", "court": "acb-hyd", "judge": "J-TBR", "type": "Criminal trial (ACB)", "value": amt,
        "subject": f"Section 7 Prevention of Corruption Act — alleged demand of {fmt_inr(amt)} by a Mandal Revenue Inspector; "
                   "trap proceedings recorded on a Hikvision DS-7208HGHI-K1 DVR",
        "opponent": "State, rep. by ACB Hyderabad Range", "role": "Accused",
        "case_no": f"C.C. No. {rng.randint(10, 90)} of {rng.choice([2022, 2023])}",
        "stages": ["Framing of charges", "Evidence of decoy (PW-1)", "Evidence of mediators", "Evidence of TLO",
                   "Section 313 examination", "Arguments"],
        "facts": ["The phenolphthalein test report and the DVR footage are the core of the prosecution case."],
        "docs": ["Section 65B certificate for DVR footage", "FSL report on the DVR (Hikvision DS-7208HGHI-K1)",
                 "Sanction order under Section 19 PC Act", "Pre-trap and post-trap mediator reports"],
    }


def gen_labour(i, client):
    return {
        "title": f"{client} vs. {rng.choice(['Greenfield Agro Industries', 'Deccan Logistics Pvt. Ltd.'])}",
        "court": "labour-hyd", "judge": "J-LNS", "type": "Industrial dispute", "value": rng.choice([640000, 980000]),
        "subject": "Challenge to termination of a JCB 3DX backhoe operator after an incident with a Kirloskar 125 kVA DG set",
        "opponent": "Management", "role": "Workman",
        "case_no": f"I.D. No. {rng.randint(20, 300)} of {rng.choice([2022, 2023])}",
        "stages": ["Counter of management", "Workman's evidence", "Management's evidence", "Arguments"],
        "facts": ["No domestic enquiry was held before the termination order."],
        "docs": ["Appointment order", "Termination order", "Attendance register extract", "Logbook of the DG set"],
    }


GENERATORS = [gen_ni_act] * 10 + [gen_civil] * 9 + [gen_mact] * 6 + [gen_consumer] * 6 + [gen_family] * 5 + \
             [gen_writ] * 3 + [gen_acb] * 2 + [gen_labour] * 2

COUNSEL_FOR_COURT = {
    "nampally-ni": ["C-MSG", "C-SAH", "C-RJK", "C-AFR"], "ccc-hyd": ["C-VPR", "C-JVR", "C-RJK"],
    "rr-lbnagar": ["C-VPR", "C-JVR", "C-SAH"], "mact-hyd": ["C-TKM"], "cdrc-hyd": ["C-AFR", "C-RJK"],
    "family-sec": ["C-SAH", "C-AFR"], "tshc": ["C-GVS"], "acb-hyd": ["C-NRS"], "labour-hyd": ["C-JVR", "C-MSG"],
}


def templated_cases(n_offset):
    cases, hearings = [], []
    clients = CLIENTS[:]
    rng.shuffle(clients)
    for i, gen in enumerate(GENERATORS):
        client = clients[i % len(clients)]
        spec = gen(i, client)
        cid = f"case-{i + 1:03d}"
        opp_counsel = rng.choice(COUNSEL_FOR_COURT[spec["court"]])
        habit = COUNSEL[opp_counsel]["habit"]
        judge = spec["judge"]
        traits = JUDGES[judge]["traits"]
        n = rng.randint(5, 16)
        disposed = rng.random() < 0.15
        next_days = None if disposed else -rng.choice([0, 0, 1, 2, 3, 5, 8, 14, 21, 30, 45])
        last = rng.randint(20, 75) if not disposed else rng.randint(40, 200)
        gaps = [rng.randint(35, 95) for _ in range(n)]
        days = [last + sum(gaps[k + 1:]) for k in range(n)]
        stage_idx = 0
        open_due = []
        for k in range(n):
            no = k + 1
            stage = spec["stages"][min(stage_idx, len(spec["stages"]) - 1)]
            adj, asked, due, promises, notes, opp_args, lesson = None, [], [], [], "", [], ""
            roll = rng.random()
            if roll < 0.34:
                ground, reason = rng.choice(HABIT_ADJ_REASONS[habit])
                adj = {"by": "opposing", "counsel": opp_counsel, "ground": ground, "reason": reason}
                notes = f"Listed for {stage.lower()}. Opposite counsel {COUNSEL[opp_counsel]['name']} sought time: {reason}."
            elif roll < 0.42:
                adj = {"by": "court", "counsel": None, "ground": "court",
                       "reason": rng.choice(["the presiding officer was on leave", "the court was busy with a part-heard sessions case",
                                             "the lawyers' association abstained from work"])}
                notes = f"Listed for {stage.lower()}, but {adj['reason']}. Matter adjourned without proceedings."
            elif roll < 0.47:
                adj = {"by": "ours", "counsel": None, "ground": "documents",
                       "reason": "we sought time as the client had not yet collected certified copies"}
                notes = f"Listed for {stage.lower()}. We sought a short date; certified copies were still awaited."
            else:
                notes = f"{stage} taken up. " + rng.choice([
                    "Proceedings went as planned.", "The court heard both sides briefly.",
                    "Witness examined; nothing adverse came out.", "Recorded; the other side did not seriously contest.",
                ])
                if k == 1 and spec["facts"]:
                    notes += " " + spec["facts"][0]
                stage_idx += 1
            if rng.random() < 0.45:
                asked.append(rng.choice(JUDGE_REMARKS[rng.choice(traits)]))
            if rng.random() < 0.3 and spec["docs"]:
                doc = rng.choice(spec["docs"])
                who = rng.choice(["us", "opposite party"])
                due.append({"item": doc, "by": who, "status": "pending"})
                open_due.append(doc)
                asked.append(f"{'We' if who == 'us' else 'The opposite party'} to file: {doc}.")
            if open_due and rng.random() < 0.3:
                done = open_due.pop(0)
                notes += f" {done} filed and taken on record."
            if rng.random() < 0.18:
                promises.append(rng.choice([
                    "Promised client a call after collecting the certified copy of the order.",
                    "Told client to bring original documents to chambers before the next date.",
                    "Promised client an estimate of the likely timeline for the next stage.",
                    "Agreed to send client a WhatsApp summary of the proceedings.",
                ]))
            if habit == "late-compilation" and rng.random() < 0.2:
                opp_args.append("Opposite counsel handed over a bulky compilation of judgments only in court.")
            if habit == "maintainability" and rng.random() < 0.25:
                opp_args.append("Opposite counsel again raised the objection that the suit / petition is not maintainable.")
            if adj and adj["by"] == "opposing" and rng.random() < 0.3:
                lesson = "Ask the court to record who sought the adjournment; it matters for costs later."
            hearings.append({
                "id": f"{cid.upper()}-H{no:02d}", "case_id": cid, "no": no, "date": d(days[k]), "judge": judge,
                "counsel": opp_counsel, "stage": stage, "notes": notes.strip(), "asked": asked, "adjournment": adj,
                "opp_args": opp_args, "our_args": [], "due": due, "promises": promises,
                "outcome": ("Adjourned." if adj else "Proceeded; posted for the next stage."), "lesson": lesson,
            })
        cases.append({
            "id": cid, "title": spec["title"], "short": spec["title"].split(" vs. ")[0].split()[-1],
            "case_no": spec["case_no"], "cnr": f"TS{rng.choice(['HY', 'RR', 'SC'])}0{rng.randint(1, 9)}{rng.randint(100000, 999999)}20{spec['case_no'][-2:]}",
            "crime": None, "court": spec["court"], "judge": judge, "type": spec["type"], "subject": spec["subject"],
            "client": {"name": client, "role": spec["role"], "phone": f"+91 9{rng.randint(100000000, 999999999)}"},
            "opponent": spec["opponent"], "opp_counsel": opp_counsel, "other_counsel": [], "value": spec["value"],
            "filed": d(days[0] + rng.randint(20, 90)),
            "status": "Disposed" if disposed else spec["stages"][min(stage_idx, len(spec["stages"]) - 1)],
            "summary": spec["subject"] + ". " + " ".join(spec["facts"]),
            "next_date": None if disposed else d(next_days),
            "next_purpose": None if disposed else spec["stages"][min(stage_idx, len(spec["stages"]) - 1)],
        })
    return cases, hearings


def main():
    cases, hearings = [], []
    c, h = reddy_case()
    cases.append(c)
    hearings += h
    for fn in (chary_pattern_cases, bail_cases):
        cs, hs = fn()
        cases += cs
        hearings += hs
    cs, hs = templated_cases(len(cases))
    cases += cs
    hearings += hs

    # Hearing dates must be strictly increasing within a case.
    by_case = {}
    for x in hearings:
        by_case.setdefault(x["case_id"], []).append(x)
    for cid, hs in by_case.items():
        dates = [x["date"] for x in sorted(hs, key=lambda x: x["no"])]
        assert dates == sorted(dates) and len(set(dates)) == len(dates), cid

    data = {
        "anchor": ANCHOR.isoformat(),
        "advocate": ADVOCATE,
        "courts": COURTS,
        "judges": {k: {kk: vv for kk, vv in v.items()} for k, v in JUDGES.items()},
        "counsel": COUNSEL,
        "cases": cases,
        "hearings": hearings,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    adj = sum(1 for x in hearings if x["adjournment"])
    print(f"{len(cases)} cases, {len(hearings)} hearings, {adj} adjournments -> {OUT}")


if __name__ == "__main__":
    main()
