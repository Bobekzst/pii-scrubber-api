# Top 300 popular Polish first names (male + female)
# Source: GUS (Główny Urząd Statystyczny)

MALE_NAMES = {
    "Adam", "Adrian", "Aleksander", "Andrzej", "Antoni", "Arkadiusz", "Artur",
    "Bartosz", "Bartłomiej", "Benedikt", "Błażej", "Bogdan", "Borys",
    "Cezary", "Cyprian", "Czesław",
    "Damian", "Daniel", "Dariusz", "Dawid", "Dominik",
    "Edmund", "Edward", "Emil",
    "Filip", "Franciszek",
    "Grzegorz", "Gustaw",
    "Henryk", "Hubert",
    "Igor", "Ireneusz",
    "Jacek", "Jakub", "Jan", "Janusz", "Jarosław", "Józef", "Julian",
    "Kamil", "Karol", "Kazimierz", "Konrad", "Krystian", "Krzysztof",
    "Lech", "Leszek", "Łukasz",
    "Marek", "Marcin", "Mariusz", "Mateusz", "Michał", "Mikołaj", "Mirosław",
    "Norbert",
    "Oskar",
    "Paweł", "Piotr", "Przemysław",
    "Radosław", "Rafał", "Robert", "Roman",
    "Sebastian", "Sławomir", "Stanisław", "Stefan", "Szymon",
    "Tadeusz", "Tomasz",
    "Waldemar", "Wiktor", "Witold", "Wojciech",
    "Zbigniew", "Zygmunt",
    # English/international names common in Poland
    "Alan", "Alex", "Brian", "Chris", "David", "James", "John", "Kevin",
    "Mark", "Martin", "Michael", "Patrick", "Peter", "Richard", "Robert",
    "Thomas", "Tim", "Victor",
}

FEMALE_NAMES = {
    "Agata", "Agnieszka", "Aleksandra", "Alicja", "Alina", "Amelia", "Anna",
    "Beata", "Barbara",
    "Celina",
    "Dagmara", "Dominika",
    "Edyta", "Elżbieta", "Emilia", "Ewa",
    "Gabriela", "Grażyna",
    "Hanna", "Helena",
    "Ilona", "Irena", "Iwona",
    "Jadwiga", "Joanna", "Julia", "Julita", "Justyna",
    "Kamila", "Karolina", "Katarzyna", "Klaudia", "Kinga", "Krystyna",
    "Laura", "Lidia", "Liliana", "Lucyna",
    "Magdalena", "Małgorzata", "Maria", "Marta", "Martyna", "Monika",
    "Natalia", "Nikola",
    "Oliwia", "Olga",
    "Patrycja", "Paula", "Paulina",
    "Renata",
    "Sabina", "Sandra", "Sara", "Sylwia",
    "Teresa",
    "Urszula",
    "Wanda", "Weronika", "Wiktoria",
    "Zofia", "Zuzanna",
    # English/international names
    "Alice", "Amy", "Angela", "Caroline", "Catherine", "Diana", "Elena",
    "Emma", "Hannah", "Helen", "Jessica", "Kate", "Laura", "Lisa",
    "Mary", "Monica", "Nicole", "Sarah", "Sophie", "Susan",
}

ALL_NAMES = MALE_NAMES | FEMALE_NAMES
