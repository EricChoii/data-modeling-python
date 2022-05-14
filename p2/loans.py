import json
import csv
import pandas as pd
import zipfile  # , ZIP_DEFLATED
import io

race_lookup = {
    "1": "American Indian or Alaska Native",
    "2": "Asian",
    "21": "Asian Indian",
    "22": "Chinese",
    "23": "Filipino",
    "24": "Japanese",
    "25": "Korean",
    "26": "Vietnamese",
    "27": "Other Asian",
    "3": "Black or African American",
    "4": "Native Hawaiian or Other Pacific Islander",
    "41": "Native Hawaiian",
    "42": "Guamanian or Chamorro",
    "43": "Samoan",
    "44": "Other Pacific Islander",
    "5": "White",
}


def read_loans(zipname, csvname, lei):
    with zipfile.ZipFile(zipname) as zf:
        with zf.open(csvname) as f:
            reader = csv.DictReader(io.TextIOWrapper(f))
            for row in reader:
                if row["lei"] == lei:
                    try:
                        yield row
                    except ValueError:
                        pass


def GetRaceLst(fields, k):
    # This function looks at the list 'fields' and
    # returns a list of values with respect to keys with the prefix 'k'
    # If the value is empty, then remove it
    out = list({val for key, val in fields.items() if key.startswith(k)})
    for null in out:
        if null == '':
            out.remove(null)
    return out


class Applicant:
    def __init__(self, age, race):
        self.age = age
        self.race = set()
        for r in race:
            if r in race_lookup.keys():
                self.race.add(race_lookup.get(r))

    def __repr__(self):
        return f"Applicant({repr(self.age)}, {repr(sorted(list(self.race)))})"

    def __lt__(self, other):
        return self.lower_age() < other.lower_age()

    def lower_age(self):
        return int(self.age.replace('<', "").replace('>', "").split('-')[0])


class Loan:
    def __init__(self, fields):
        # missing values
        mssval = ['NA', 'Exempt']

        # attribute assignment
        la = fields["loan_amount"]
        self.loan_amount = -1 if la in mssval else float(la)
        pv = fields["property_value"]
        self.property_value = -1 if pv in mssval else float(pv)
        ir = fields["interest_rate"]
        self.interest_rate = -1 if ir in mssval else float(ir)

        a1 = Applicant(fields["applicant_age"],
                       GetRaceLst(fields, "applicant_race-"))
        applicant = [a1]
        if fields["co-applicant_age"] != "9999":
            a2 = Applicant(fields["co-applicant_age"],
                           GetRaceLst(fields, "co-applicant_race-"))
            applicant.append(a2)
        self.applicants = applicant

    def __str__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"

    def __repr__(self):
        return f"<Loan: {repr(self.interest_rate)}% on ${repr(self.property_value)} with {repr(len(self.applicants))} applicant(s)>"

    def yearly_amounts(self, yearly_payment):
        # TODO: assert interest and amount are positive
        assert self.interest_rate > 0 and self.loan_amount > 0, "either interest or amount is negative"

        amt = self.loan_amount
        while amt > 0:
            yield amt
            # TODO: add interest rate multiplied by amt to amt
            amt += amt * self.interest_rate / 100
            # TODO: subtract yearly payment from amt
            amt -= yearly_payment


class Bank:
    def __init__(self, name):
        # Load JSON data
        with open("banks.json") as f:
            banks = json.load(f)

        # Add a Loan object
        for b in banks:
            bn = b['name']
            if bn == name:
                self.lei = b['lei']
                break

        # Initilize a list of loans data
        self.loans = []

        # Get row data of the same 'lei' from .csv
        # Then, add it into self.loans
        for r in read_loans('wi.zip', 'wi.csv', self.lei):
            self.loans.append(Loan(r))

    def __len__(self):
        return len(self.loans)

    def __getitem__(self, lookup):
        return self.loans[lookup]
