from faker import Faker

fake = Faker()

DISCLAIMER = "Mock/Test Data — Not a real identity. For development & testing purposes only."

class TestDataService:
    @staticmethod
    def generate_names(count: int = 10, gender: str = "all") -> list[dict]:
        count = max(1, min(100, count))
        results = []
        for _ in range(count):
            if gender == "male":
                first = fake.first_name_male()
            elif gender == "female":
                first = fake.first_name_female()
            else:
                first = fake.first_name()
            last = fake.last_name()
            results.append({
                "fullName": f"{first} {last}",
                "firstName": first,
                "lastName": last,
                "prefix": fake.prefix(),
                "disclaimer": DISCLAIMER
            })
        return results

    @staticmethod
    def generate_addresses(count: int = 5) -> list[dict]:
        count = max(1, min(50, count))
        results = []
        for _ in range(count):
            results.append({
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "stateCode": fake.state_abbr(),
                "zipCode": fake.postcode(),
                "country": fake.country(),
                "fullAddress": fake.address().replace('\n', ', '),
                "disclaimer": DISCLAIMER
            })
        return results

    @staticmethod
    def generate_phones(count: int = 10) -> list[dict]:
        count = max(1, min(100, count))
        results = []
        for _ in range(count):
            results.append({
                "phoneNumber": fake.phone_number(),
                "countryCode": "+1",
                "disclaimer": DISCLAIMER
            })
        return results

    @staticmethod
    def generate_emails(count: int = 10) -> list[dict]:
        count = max(1, min(100, count))
        results = []
        for _ in range(count):
            results.append({
                "email": fake.safe_email(),
                "freeEmail": fake.free_email(),
                "disclaimer": DISCLAIMER
            })
        return results

    @staticmethod
    def generate_companies(count: int = 5) -> list[dict]:
        count = max(1, min(50, count))
        results = []
        for _ in range(count):
            results.append({
                "name": fake.company(),
                "suffix": fake.company_suffix(),
                "catchPhrase": fake.catch_phrase(),
                "bs": fake.bs(),
                "industry": fake.job(),
                "disclaimer": DISCLAIMER
            })
        return results

    @staticmethod
    def generate_custom_json(fields: list[str], count: int = 10) -> list[dict]:
        count = max(1, min(100, count))
        records = []
        for _ in range(count):
            row = {}
            for field in fields:
                field_lower = field.lower()
                if "id" in field_lower:
                    row[field] = fake.uuid4()
                elif "name" in field_lower:
                    row[field] = fake.name()
                elif "email" in field_lower:
                    row[field] = fake.safe_email()
                elif "phone" in field_lower:
                    row[field] = fake.phone_number()
                elif "address" in field_lower or "street" in field_lower:
                    row[field] = fake.street_address()
                elif "city" in field_lower:
                    row[field] = fake.city()
                elif "country" in field_lower:
                    row[field] = fake.country()
                elif "company" in field_lower:
                    row[field] = fake.company()
                elif "job" in field_lower or "role" in field_lower:
                    row[field] = fake.job()
                elif "date" in field_lower:
                    row[field] = str(fake.date_this_decade())
                else:
                    row[field] = fake.word()
            records.append(row)
        return records
