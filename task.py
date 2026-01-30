import pickle
from pathlib import Path
from collections import UserDict
from datetime import datetime, date, timedelta


# ===================== CLASSES (HW6 base) =====================
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        value = str(value)
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must contain 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            dt = datetime.strptime(str(value), "%d.%m.%Y").date()
            super().__init__(dt.strftime("%d.%m.%Y"))
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    @property
    def date(self) -> date:
        return datetime.strptime(self.value, "%d.%m.%Y").date()


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone not found.")

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Old phone not found.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "no phones"
        bday_str = self.birthday.value if self.birthday else "no birthday"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {bday_str}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str):
        self.data.pop(name, None)

    def get_upcoming_birthdays(self):
        """
        Дні народження на 7 днів вперед включно з поточним днем.
        Якщо припадає на вихідний — переносимо дату привітання на найближчий понеділок.
        Повертає: [{"name": "...", "birthday": "DD.MM.YYYY"}, ...]
        де birthday = дата ПРИВІТАННЯ.
        """
        today = date.today()
        end = today + timedelta(days=7)
        result = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday = record.birthday.date
            next_bday = bday.replace(year=today.year)
            if next_bday < today:
                next_bday = next_bday.replace(year=today.year + 1)

            if today <= next_bday <= end:
                congrat_day = next_bday

                if congrat_day.weekday() == 5:        # Saturday
                    congrat_day += timedelta(days=2)
                elif congrat_day.weekday() == 6:      # Sunday
                    congrat_day += timedelta(days=1)

                result.append({
                    "name": record.name.value,
                    "birthday": congrat_day.strftime("%d.%m.%Y")
                })

        result.sort(key=lambda x: datetime.strptime(x["birthday"], "%d.%m.%Y").date())
        return result

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values()) if self.data else "Address book is empty."


# ===================== SAVE / LOAD (HW8) =====================
DATA_FILE = Path("addressbook.pkl")


def save_data(book: AddressBook, filename: Path = DATA_FILE) -> None:
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename: Path = DATA_FILE) -> AddressBook:
    try:
        with open(filename, "rb") as f:
            book = pickle.load(f)
            if not isinstance(book, AddressBook):
                return AddressBook()
            return book
    except FileNotFoundError:
        return AddressBook()
    except (pickle.UnpicklingError, EOFError):
        return AddressBook()


# ===================== DECORATOR =====================
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Not enough arguments."
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
    return wrapper


# ===================== PARSER =====================
def parse_input(user_input: str):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    command = parts[0].lower()
    args = parts[1:]
    return command, args


# ===================== HANDLERS =====================
@input_error
def add_contact(args, book: AddressBook):
    name, phone = args[0], args[1]
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        return "Contact added."
    record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Phone number changed."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.phones:
        return "No phones for this contact."
    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(args, book: AddressBook):
    return str(book)


@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(bday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "Birthday is not set."
    return record.birthday.value


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(f'{item["name"]}: {item["birthday"]}' for item in upcoming)


# ===================== MAIN =====================
def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    try:
        while True:
            user_input = input("Enter a command: ")
            command, args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(args, book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(args, book))

            else:
                print("Invalid command.")

    except KeyboardInterrupt:
        print("\nInterrupted. Saving data...")

    finally:
        save_data(book)


if __name__ == "__main__":
    main()
