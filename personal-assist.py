import pickle
from collections import UserDict
import re
from datetime import datetime
from difflib import SequenceMatcher


def handle_user_input(validation_class=None):
    """Декоратор для обробки користувацького вводу з дружніми повідомленнями."""

    def decorator(func):
        def wrapper(prompt):
            while True:
                user_input = input(prompt)
                command = suggest_command(user_input)
                if command == 'вийти':
                    print("Вихід з поточної дії. Повертаємося в головне меню.")
                    return 'exit'
                if command == 'відміна':
                    print("Дію скасовано. Повертаємося в головне меню.")
                    return None
                if validation_class:
                    try:
                        validation_class(user_input)
                    except ValueError as e:
                        print(f"Помилка вводу: {
                              e}. Будь ласка, спробуйте ще раз.")
                        continue
                return func(user_input)
        return wrapper
    return decorator


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if len(value) < 2:
            raise ValueError("Ім'я повинно містити мінімум 2 літери.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not re.match(r"^\d{10}$", value):
            raise ValueError("Номер телефону має містити рівно 10 цифр.")
        super().__init__(value)


class Email(Field):
    def __init__(self, value):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Некоректний формат email. "
                             "Правильний формат: example@domain.com.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, '%d-%m-%Y').date()
        except ValueError:
            raise ValueError(
                "День народження повинен бути в форматі дд-мм-рррр.")
        super().__init__(self.value)


class Address(Field):
    def __init__(self, value):
        if len(value) < 5:
            raise ValueError("Адреса повинна містити мінімум 5 символів.")
        super().__init__(value)


class Note:
    def __init__(self, text, tags=None):
        self.text = text
        self.tags = tags if tags else []

    def __str__(self):
        tags_str = ', '.join(self.tags)
        return f"Нотатка: {self.text}, Теги: {tags_str}"

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def edit_text(self, new_text):
        self.text = new_text

    def edit_tags(self, new_tags):
        self.tags = new_tags


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.address = None
        self.email = None
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def edit_phone(self, old_phone, new_phone):
        for i, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return True
        return False

    def add_address(self, address):
        self.address = Address(address)

    def edit_address(self, new_address):
        self.address = Address(new_address)

    def add_email(self, email):
        self.email = Email(email)

    def edit_email(self, new_email):
        self.email = Email(new_email)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def edit_birthday(self, new_birthday):
        self.birthday = Birthday(new_birthday)

    def edit_name(self, new_name):
        self.name = Name(new_name)

    def days_to_birthday(self):
        if not self.birthday:
            return None
        today = datetime.today().date()
        next_birthday = self.birthday.value.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        address = self.address.value if self.address else "N/A"
        email = self.email.value if self.email else "N/A"
        birthday = self.birthday.value.strftime(
            '%d-%m-%Y') if self.birthday else "N/A"
        return (f"Контакт: {self.name.value}, телефони: {phones}, "
                f"адреса: {address}, email: {email}, день народження: {birthday}")


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return True
        return False

    def search(self, keyword, criterion="name"):
        results = []
        for record in self.data.values():
            if criterion == "name" and keyword.lower() in record.name.value.lower():
                results.append(record)
            elif criterion == "phone" and any(keyword in phone.value for phone in record.phones):
                results.append(record)
            elif criterion == "email" and keyword.lower() in record.email.value.lower():
                results.append(record)
            elif criterion == "address" and keyword.lower() in record.address.value.lower():
                results.append(record)
        return results

    def search_by_birthday(self, days):
        today = datetime.today().date()
        results = []
        for record in self.data.values():
            days_to_birthday = record.days_to_birthday()
            if days_to_birthday is not None and days_to_birthday <= days:
                results.append(record)
        return results

    def show_all_contacts(self):
        if not self.data:
            return "Ваша адресна книга порожня."
        return "\n".join([str(record) for record in self.data.values()])

    def __getstate__(self):
        return self.data

    def __setstate__(self, state):
        self.data = state


class NoteBook(UserDict):
    def add_note(self, note):
        self.data[note.text] = note

    def delete(self, text):
        if text in self.data:
            del self.data[text]
            return True
        return False

    def find(self, text):
        return self.data.get(text, None)

    def search(self, keyword):
        results = []
        for note in self.data.values():
            if keyword.lower() in note.text.lower() or \
               any(keyword.lower() in tag for tag in note.tags):
                results.append(note)
        return results

    def __getstate__(self):
        return self.data

    def __setstate__(self, state):
        self.data = state


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def suggest_command(user_input):
    keywords = {
        'додати контакт': ['додати контакт', 'створити контакт', 'новий контакт',
                           'ввести контакт', 'записати контакт', 'добавити контакт',
                           'додати користувача', 'добавити користувача', 'ввести користувача',
                           'новий користувач', 'ввезти контакт', 'введ контакт',
                           'контакт новий', 'корист новий', 'користувача новий',
                           'контакт користувача', 'новий запис користувача'],
        'знайти контакт': ['знайти контакт', 'пошук контакт', 'шукати контакт',
                           'відшукати контакт', 'знайти користувача', 'пошук користувача',
                           'шукати користувача', 'відшукати користувача', 'пошукати контакт',
                           'пошукати користувача', 'пошук контактів', 'відшукати контакти',
                           'пошук користувачів', 'відшукати користувачів'],
        'видалити контакт': ['видалити контакт', 'знищити контакт', 'стерти контакт',
                             'вилучити контакт', 'видалити користувача', 'знищити користувача',
                             'стерти користувача', 'вилучити користувача', 'видалити запис',
                             'стерти запис', 'видалення контакту', 'стерти контакти',
                             'видалення записів', 'стерти записи', 'вилучити контакти',
                             'знищити записи'],
        'редагувати контакт': ['редагувати контакт', 'змінити контакт', 'редагування контакту',
                               'редактировать контакт', 'змінити запис', 'змінити ім\'я',
                               'змінити номер', 'змінити email', 'змінити адресу',
                               'редагувати номер', 'редагувати ім\'я', 'редагувати email',
                               'редагувати адресу', 'редактирование контакта'],
        'редагувати нотатку': ['редагувати нотатку', 'змінити нотатку', 'редагування нотатки',
                               'редактировать нотатку', 'змінити текст', 'змінити теги',
                               'редагувати текст', 'редагувати теги', 'редагування тексту',
                               'редагування тегів', 'змінити запис нотатки'],
        'дні народження': ['дні народження', 'показати дні народження',
                           'знайти дні народження', 'пошук днів народження',
                           'найближчі дні народження', 'наступні дні народження',
                           'вивести дні народження', 'народження контакту',
                           'найближчі дати народження', 'найближчі свята',
                           'дні народження контакту', 'найближчі події',
                           'найближчі свята контакту', 'наступні свята',
                           'вивести дні народження контакту'],
        'додати нотатку': ['додати нотатку', 'створити нотатку', 'нова нотатка',
                           'ввести нотатку', 'записати нотатку', 'добавити нотатку',
                           'новий запис', 'ввести запис', 'записати запис', 'новий текст',
                           'створити запис нотатки', 'добавити новий запис',
                           'новий текст нотатки'],
        'знайти нотатку': ['знайти нотатку', 'пошук нотатки', 'шукати нотатку',
                           'відшукати нотатку', 'знайти запис', 'пошук запису',
                           'шукати запис', 'відшукати запис', 'пошукати нотатку',
                           'пошукати запис', 'знайти текст нотатки', 'відшукати текст',
                           'пошук тексту', 'пошук записів', 'знайти записи нотаток'],
        'видалити нотатку': ['видалити нотатку', 'знищити нотатку', 'стерти нотатку',
                             'вилучити нотатку', 'видалити запис', 'знищити запис',
                             'стерти запис', 'вилучити запис', 'стерти текст',
                             'видалити текст', 'видалити текст нотатки', 'стерти текст нотатки',
                             'вилучити запис нотатки'],
        'вийти': ['вийти', 'закрити', 'завершити', 'припинити', 'вихід',
                  'закрити програму', 'виходити', 'exit', 'close', 'завершення',
                  'вихід з програми', 'припинити роботу', 'завершити роботу',
                  'вийти з програми', 'закрити все'],
        'відміна': ['відміна', 'отмена', 'cancel', 'відмінити', 'зупинити',
                    'скасувати', 'скасування', 'зупинка', 'перервати',
                    'скасувати операцію', 'відмінити операцію', 'скасування дії',
                    'відміна дії', 'скасувати введення', 'відмінити введення',
                    'зупинити введення', 'перервати введення'],
        'показати всі контакти': ['показати всі контакти', 'всі контакти',
                                  'переглянути всі контакти', 'переглянути контакти',
                                  'відобразити всі контакти', 'показати список контактів',
                                  'вивести всі контакти', 'вивести список контактів',
                                  'показати контакти', 'список контактів']
    }

    best_match = None
    highest_similarity = 0.0

    for command, command_list in keywords.items():
        for keyword in command_list:
            similarity = similar(user_input.lower(), keyword.lower())
            if similarity > highest_similarity and similarity >= 0.3:
                highest_similarity = similarity
                best_match = command

    return best_match


@handle_user_input(Name)
def get_name(user_input):
    return user_input


@handle_user_input(Phone)
def get_phone(user_input):
    return user_input


@handle_user_input(Address)
def get_address(user_input):
    return user_input


@handle_user_input(Email)
def get_email(user_input):
    return user_input


@handle_user_input(Birthday)
def get_birthday(user_input):
    return user_input


def main():
    book = load_data('addressbook.pkl', AddressBook)
    notebook = load_data('notebook.pkl', NoteBook)
    print("Ласкаво просимо до персонального помічника! Я тут, щоб допомогти вам з вашими контактами та нотатками.")

    while True:
        user_input = input("\nБудь ласка, введіть команду >>> ")
        command = suggest_command(user_input)

        if not command:
            print(
                "Вибачте, я не зміг розпізнати команду. Можливо, ви мали на увазі щось інше? Спробуйте ще раз.")
            continue

        if command == 'додати контакт':
            name = get_name("Введіть ім'я: ")
            if name in ['exit', None]:
                continue
            phone = get_phone("Введіть номер телефону: ")
            if phone in ['exit', None]:
                continue
            address = get_address("Введіть адресу: ")
            if address in ['exit', None]:
                continue
            email = get_email("Введіть email: ")
            if email in ['exit', None]:
                continue
            birthday = get_birthday("Введіть день народження (дд-мм-рррр): ")
            if birthday in ['exit', None]:
                continue
            record = Record(name)
            record.add_phone(phone)
            record.add_address(address)
            record.add_email(email)
            record.add_birthday(birthday)
            book.add_record(record)
            print(f"Контакт {name} успішно додано до вашої адресної книги!")

        elif command == 'знайти контакт':
            print("Оберіть критерій пошуку:")
            print("1. Пошук за іменем")
            print("2. Пошук за номером телефону")
            print("3. Пошук за email")
            print("4. Пошук за адресою")
            criterion_choice = input("Введіть номер критерію: ")

            if criterion_choice == "1":
                criterion = "name"
                keyword = input("Введіть ім'я для пошуку: ")
            elif criterion_choice == "2":
                criterion = "phone"
                keyword = input("Введіть номер телефону для пошуку: ")
            elif criterion_choice == "3":
                criterion = "email"
                keyword = input("Введіть email для пошуку: ")
            elif criterion_choice == "4":
                criterion = "address"
                keyword = input("Введіть адресу для пошуку: ")
            else:
                print("Невірний критерій. Спробуйте ще раз.")
                continue

            if suggest_command(keyword) == 'вийти' or suggest_command(keyword) == 'відміна':
                print("Пошук скасовано. Повертаємося до головного меню.")
                continue

            results = book.search(keyword, criterion)
            if results:
                for record in results:
                    print(record)
            else:
                print("На жаль, не вдалося знайти контакт за вашим запитом.")

        elif command == 'видалити контакт':
            name = input("Введіть ім'я для видалення: ")
            if suggest_command(name) == 'вийти' or suggest_command(name) == 'відміна':
                print("Видалення скасовано. Повертаємося до головного меню.")
                continue
            if book.delete(name):
                print(f"Контакт {name} успішно видалено.")
            else:
                print("Не вдалося знайти контакт з таким ім'ям для видалення.")

        elif command == 'редагувати контакт':
            name = input("Введіть ім'я контакту, який потрібно редагувати: ")
            record = book.find(name)
            if not record:
                print("Контакт не знайдено.")
                continue

            print("Оберіть поле для редагування:")
            print("1. Ім'я")
            print("2. Номер телефону")
            print("3. Email")
            print("4. Адреса")
            print("5. День народження")
            field_choice = input("Введіть номер поля: ")

            if field_choice == "1":
                new_name = get_name("Введіть нове ім'я: ")
                if new_name not in ['exit', None]:
                    record.edit_name(new_name)
                    print("Ім'я успішно змінено.")
            elif field_choice == "2":
                old_phone = get_phone(
                    "Введіть номер телефону, який потрібно замінити: ")
                new_phone = get_phone("Введіть новий номер телефону: ")
                if old_phone not in ['exit', None] and new_phone not in ['exit', None]:
                    if record.edit_phone(old_phone, new_phone):
                        print("Номер телефону успішно змінено.")
                    else:
                        print("Старий номер телефону не знайдено.")
            elif field_choice == "3":
                new_email = get_email("Введіть новий email: ")
                if new_email not in ['exit', None]:
                    record.edit_email(new_email)
                    print("Email успішно змінено.")
            elif field_choice == "4":
                new_address = get_address("Введіть нову адресу: ")
                if new_address not in ['exit', None]:
                    record.edit_address(new_address)
                    print("Адресу успішно змінено.")
            elif field_choice == "5":
                new_birthday = get_birthday(
                    "Введіть новий день народження (дд-мм-рррр): ")
                if new_birthday not in ['exit', None]:
                    record.edit_birthday(new_birthday)
                    print("День народження успішно змінено.")
            else:
                print("Невірний вибір. Спробуйте ще раз.")

        elif command == 'редагувати нотатку':
            text = input("Введіть текст нотатки, яку потрібно редагувати: ")
            note = notebook.find(text)
            if not note:
                print("Нотатку не знайдено.")
                continue

            print("Оберіть поле для редагування:")
            print("1. Текст нотатки")
            print("2. Теги")
            field_choice = input("Введіть номер поля: ")

            if field_choice == "1":
                new_text = input("Введіть новий текст нотатки: ")
                if new_text not in ['exit', None]:
                    note.edit_text(new_text)
                    notebook.add_note(note)
                    notebook.delete(text)
                    print("Текст нотатки успішно змінено.")
            elif field_choice == "2":
                new_tags = input("Введіть нові теги через кому: ").split(',')
                if new_tags not in ['exit', None]:
                    note.edit_tags(new_tags)
                    print("Теги успішно змінено.")
            else:
                print("Невірний вибір. Спробуйте ще раз.")

        elif command == 'дні народження':
            days = input("Введіть кількість днів: ")
            if suggest_command(days) == 'вийти' or suggest_command(days) == 'відміна':
                print("Дія скасована. Повертаємося до головного меню.")
                continue
            try:
                days = int(days)
            except ValueError:
                print("Будь ласка, введіть числове значення. Спробуйте ще раз.")
                continue
            upcoming_birthdays = book.search_by_birthday(days)
            if upcoming_birthdays:
                print(f"Знайдено контакти з днями народження в наступні {
                      days} днів:")
                for record in upcoming_birthdays:
                    print(record)
            else:
                print("Контактів з днями народження у зазначений період не знайдено.")

        elif command == 'додати нотатку':
            text = input("Введіть текст нотатки: ")
            if suggest_command(text) == 'вийти' or suggest_command(text) == 'відміна':
                print("Додавання нотатки скасовано. Повертаємося до головного меню.")
                continue
            tags = input("Введіть теги через кому: ").split(',')
            if suggest_command(','.join(tags)) == 'вийти' or suggest_command(','.join(tags)) == 'відміна':
                print("Додавання тегів скасовано. Повертаємося до головного меню.")
                continue
            note = Note(text, tags)
            notebook.add_note(note)
            print(f"Нотатку успішно додано!")

        elif command == 'знайти нотатку':
            keyword = input("Введіть ключове слово для пошуку нотатки: ")
            if suggest_command(keyword) == 'вийти' or suggest_command(keyword) == 'відміна':
                print("Пошук нотатки скасовано. Повертаємося до головного меню.")
                continue
            results = notebook.search(keyword)
            if results:
                print("Знайдені нотатки:")
                for note in results:
                    print(note)
            else:
                print("На жаль, не вдалося знайти нотатку за вашим запитом.")

        elif command == 'видалити нотатку':
            text = input("Введіть текст нотатки для видалення: ")
            if suggest_command(text) == 'вийти' or suggest_command(text) == 'відміна':
                print("Видалення нотатки скасовано. Повертаємося до головного меню.")
                continue
            if notebook.delete(text):
                print(f"Нотатку успішно видалено.")
            else:
                print("Не вдалося знайти нотатку для видалення.")

        elif command == 'показати всі контакти':
            all_contacts = book.show_all_contacts()
            print("Ваші контакти:")
            print(all_contacts)

        elif command == 'вийти':
            save_data(book, 'addressbook.pkl')
            save_data(notebook, 'notebook.pkl')
            print("Дані збережені. До побачення! Сподіваюся, що ви скоро повернетесь!")
            break

        else:
            print("Вибачте, я не впізнаю цю команду. Спробуйте ще раз.")


def save_data(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def load_data(filename, data_class):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return data_class()


if __name__ == '__main__':
    main()
